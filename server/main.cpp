
#include <algorithm>
#include <cctype>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <ctime>
#include <fstream>
#include <iostream>
#include <map>
#include <mutex>
#include <optional>
#include <regex>
#include <sstream>
#include <string>
#include <vector>

#include "third_party/httplib.h"
#include "third_party/json.hpp"
#include "third_party/onnxruntime/include/onnxruntime_cxx_api.h"

using json = nlohmann::json;


static std::string toLower(const std::string& s) {
  std::string out = s;
  std::transform(out.begin(), out.end(), out.begin(),
                  [](unsigned char c) { return std::tolower(c); });
  return out;
}

static json loadJson(const std::string& path) {
  std::ifstream f(path);
  if (!f) {
    std::cerr << "WARNING: could not open " << path << "\n";
    return json::object();
  }
  json j;
  f >> j;
  return j;
}

static long nowEpochSeconds() {
  return std::chrono::duration_cast<std::chrono::seconds>(
             std::chrono::system_clock::now().time_since_epoch())
      .count();
}


class IntentClassifier {
 public:
  explicit IntentClassifier(const std::string& modelPath)
      : env_(ORT_LOGGING_LEVEL_WARNING, "vsa"),
        session_(nullptr) {
    Ort::SessionOptions opts;
    opts.SetIntraOpNumThreads(1);
#ifdef _WIN32
    std::wstring wModelPath(modelPath.begin(), modelPath.end());
    session_ = Ort::Session(env_, wModelPath.c_str(), opts);
#else
    session_ = Ort::Session(env_, modelPath.c_str(), opts);
#endif
  }

  std::pair<std::string, double> classify(const std::string& text) {
    try {
      Ort::AllocatorWithDefaultOptions allocator;
      std::vector<int64_t> shape = {1, 1};
      Ort::Value input = Ort::Value::CreateTensor(
          allocator, shape.data(), shape.size(),
          ONNX_TENSOR_ELEMENT_DATA_TYPE_STRING);
      const char* strs[1] = {text.c_str()};
      input.FillStringTensor(strs, 1);

      const char* inputNames[] = {"input"};
      const char* outputNames[] = {"label", "probabilities"};

      auto outputs = session_.Run(Ort::RunOptions{nullptr}, inputNames,
                                   &input, 1, outputNames, 2);

      Ort::Value& labelTensor = outputs[0];
      size_t len = labelTensor.GetStringTensorElementLength(0);
      std::string label(len, '\0');
      labelTensor.GetStringTensorElement(len, 0, label.data());

      Ort::Value& probTensor = outputs[1];
      float* probs = probTensor.GetTensorMutableData<float>();
      auto probShape = probTensor.GetTensorTypeAndShapeInfo().GetShape();
      size_t numClasses = probShape.empty() ? 0 : static_cast<size_t>(probShape.back());
      double maxProb = 0.0;
      for (size_t i = 0; i < numClasses; ++i) maxProb = std::max(maxProb, (double)probs[i]);

      return {label, maxProb};
    } catch (const std::exception& e) {
      std::cerr << "ONNX inference error: " << e.what() << "\n";
      return {"ADD", 0.0};
    }
  }

 private:
  Ort::Env env_;
  Ort::Session session_;
};


struct Dictionaries {
  json items;

  json categories;

  json brands;

  json sizes;

  json substitutes;

  json seasonal;

  json catalog;


  void loadAll(const std::string& dataDir) {
    items = loadJson(dataDir + "/items.json");
    categories = loadJson(dataDir + "/categories.json");
    brands = loadJson(dataDir + "/brands.json");
    sizes = loadJson(dataDir + "/sizes.json");
    substitutes = loadJson(dataDir + "/substitutes.json");
    seasonal = loadJson(dataDir + "/seasonal.json");
    catalog = loadJson(dataDir + "/catalog.json");
  }
};

static std::optional<std::string> findLongestMatch(const std::string& text,
                                                     const json& dict) {
  std::string best;
  std::string bestValue;
  for (auto it = dict.begin(); it != dict.end(); ++it) {
    const std::string& key = it.key();
    std::regex r("(?:^|[^a-zA-Z])" + key + "(?:$|[^a-zA-Z])");
    if (std::regex_search(text, r)) {
      if (key.size() > best.size()) {
        best = key;
        bestValue = it.value().get<std::string>();
      }
    }
  }
  if (best.empty()) return std::nullopt;
  return bestValue;
}

static std::optional<std::string> findArrayMatch(const std::string& text,
                                                   const json& arr) {
  std::string best;
  for (const auto& v : arr) {
    std::string s = v.get<std::string>();
    std::regex r("(?:^|[^a-zA-Z])" + s + "(?:$|[^a-zA-Z])");
    if (std::regex_search(text, r) && s.size() > best.size()) best = s;
  }
  if (best.empty()) return std::nullopt;
  return best;
}

struct ParsedQuantity {
  bool found = false;
  int value = 1;
};

static ParsedQuantity extractQuantity(const std::string& text) {
  ParsedQuantity q;
  static const std::regex numRe(R"(\b(\d+))");
  std::smatch m;
  if (std::regex_search(text, m, numRe)) {
    q.found = true;
    q.value = std::stoi(m[1].str());
    return q;
  }
  if (text.find("half a dozen") != std::string::npos || text.find("half dozen") != std::string::npos) {
    q.found = true;
    q.value = 6;
    return q;
  }
  if (text.find("dozen") != std::string::npos) {
    q.found = true;
    q.value = 12;
    return q;
  }
  
  const std::vector<std::pair<std::string, int>> words = {
    {"one", 1}, {"a", 1}, {"an", 1}, {"two", 2}, {"three", 3},
    {"four", 4}, {"five", 5}, {"six", 6}, {"seven", 7},
    {"eight", 8}, {"nine", 9}, {"ten", 10}
  };
  for (const auto& kv : words) {
    std::regex r("(?:^|[^a-zA-Z])" + kv.first + "(?:$|[^a-zA-Z])");
    if (std::regex_search(text, r)) {
      q.found = true;
      q.value = kv.second;
      return q;
    }
  }
  
  return q;
}

struct PriceRange {
  bool hasMin = false;
  bool hasMax = false;
  double min = 0.0;
  double max = 0.0;
};

static PriceRange extractPriceRange(const std::string& text) {
  PriceRange p;
  static const std::regex betweenRe(
      R"(between\s*\$?(\d+(?:\.\d+)?)\s*(?:and|y|aur)\s*\$?(\d+(?:\.\d+)?))");
  static const std::regex underRe(
      R"((?:under|menos de|less than)\s*\$?(\d+(?:\.\d+)?))");
  static const std::regex hindiUnderRe(
      R"(\$?(\d+(?:\.\d+)?)\s*(?:se kam|ke andar))");
  static const std::regex bareDollarRe(R"(\$(\d+(?:\.\d+)?))");

  std::smatch m;
  if (std::regex_search(text, m, betweenRe)) {
    p.hasMin = true;
    p.hasMax = true;
    p.min = std::stod(m[1].str());
    p.max = std::stod(m[2].str());
    return p;
  }
  if (std::regex_search(text, m, underRe)) {
    p.hasMax = true;
    p.max = std::stod(m[1].str());
    return p;
  }
  if (std::regex_search(text, m, hindiUnderRe)) {
    p.hasMax = true;
    p.max = std::stod(m[1].str());
    return p;
  }
  if (std::regex_search(text, m, bareDollarRe)) {
    p.hasMax = true;
    p.max = std::stod(m[1].str());
    return p;
  }
  return p;
}

struct Entities {
  std::optional<std::string> item;
  std::optional<std::string> category;
  std::optional<std::string> brand;
  std::optional<std::string> size;
  ParsedQuantity quantity;
  PriceRange priceRange;
};

static Entities extractEntities(const std::string& rawText, const Dictionaries& dict) {
  std::string text = toLower(rawText);
  Entities e;
  e.item = findLongestMatch(text, dict.items);
  if (e.item) {
    auto catIt = dict.categories.find(*e.item);
    if (catIt != dict.categories.end()) e.category = catIt->get<std::string>();
  }
  e.brand = findArrayMatch(text, dict.brands);
  e.size = findArrayMatch(text, dict.sizes);
  e.quantity = extractQuantity(text);
  e.priceRange = extractPriceRange(text);
  return e;
}


struct HistoryEvent {
  std::string item;
  long timestamp;

};

class HistoryStore {
 public:
  void loadSeed(const std::string& path) {
    json seed = loadJson(path);
    long now = nowEpochSeconds();
    std::lock_guard<std::mutex> lock(mu_);
    for (const auto& e : seed) {
      long daysAgo = e.value("days_ago", 0);
      events_.push_back({e.value("item", ""), now - daysAgo * 86400L});
    }
  }

  void log(const std::string& item) {
    std::lock_guard<std::mutex> lock(mu_);
    events_.push_back({toLower(item), nowEpochSeconds()});
  }

  std::vector<std::pair<std::string, double>> scored() const {
    std::lock_guard<std::mutex> lock(mu_);
    std::map<std::string, int> freq;
    std::map<std::string, long> lastSeen;
    long now = nowEpochSeconds();
    for (const auto& ev : events_) {
      freq[ev.item]++;
      if (!lastSeen.count(ev.item) || ev.timestamp > lastSeen[ev.item]) {
        lastSeen[ev.item] = ev.timestamp;
      }
    }
    std::vector<std::pair<std::string, double>> out;
    for (const auto& [item, count] : freq) {
      double daysSince = std::max(1.0, (now - lastSeen[item]) / 86400.0);
      double recencyScore = 1.0 / daysSince;
      double score = count * 1.0 + recencyScore * 5.0;
      out.push_back({item, score});
    }
    std::sort(out.begin(), out.end(),
              [](auto& a, auto& b) { return a.second > b.second; });
    return out;
  }

 private:
  mutable std::mutex mu_;
  std::vector<HistoryEvent> events_;
};


static std::vector<std::string> splitCsv(const std::string& s) {
  std::vector<std::string> out;
  std::stringstream ss(s);
  std::string item;
  while (std::getline(ss, item, ',')) {
    if (!item.empty()) out.push_back(toLower(item));
  }
  return out;
}

int main(int argc, char** argv) {
  std::string dataDir = "data";
  std::string modelPath = dataDir + "/model.onnx";
  std::string staticDir = "public";
  int port = 8080;

  for (int i = 1; i < argc; ++i) {
    std::string arg = argv[i];
    if (arg == "--data-dir" && i + 1 < argc) dataDir = argv[++i];
    if (arg == "--static-dir" && i + 1 < argc) staticDir = argv[++i];
    if (arg == "--port" && i + 1 < argc) port = std::stoi(argv[++i]);
  }
  if (const char* envPort = std::getenv("PORT")) port = std::stoi(envPort);

  std::cout << "Loading model from " << modelPath << " ...\n";
  IntentClassifier classifier(modelPath);

  Dictionaries dict;
  dict.loadAll(dataDir);

  HistoryStore history;
  history.loadSeed(dataDir + "/history_seed.json");

  httplib::Server svr;
  svr.set_mount_point("/", staticDir);

  svr.Post("/parse", [&](const httplib::Request& req, httplib::Response& res) {
    json body;
    try {
      body = json::parse(req.body);
    } catch (...) {
      res.status = 400;
      res.set_content(R"({"error":"invalid json"})", "application/json");
      return;
    }
    std::string text = body.value("text", "");
    auto [intent, confidence] = classifier.classify(text);
    Entities e = extractEntities(text, dict);

    json out;
    out["intent"] = intent;
    out["confidence"] = confidence;
    if (e.item) out["item"] = *e.item;
    if (e.category) out["category"] = *e.category;
    if (e.brand) out["brand"] = *e.brand;
    if (e.size) out["size"] = *e.size;
    if (intent == "ADD" || intent == "REMOVE") {
      out["quantity"] = e.quantity.value;
      out["quantity_explicit"] = e.quantity.found;
    }
    if (e.priceRange.hasMin || e.priceRange.hasMax) {
      json pr;
      if (e.priceRange.hasMin) pr["min"] = e.priceRange.min;
      if (e.priceRange.hasMax) pr["max"] = e.priceRange.max;
      out["price_range"] = pr;
    }
    res.set_content(out.dump(), "application/json");
  });

  svr.Post("/log", [&](const httplib::Request& req, httplib::Response& res) {
    json body;
    try {
      body = json::parse(req.body);
    } catch (...) {
      res.status = 400;
      res.set_content(R"({"error":"invalid json"})", "application/json");
      return;
    }
    std::string type = body.value("type", "add");
    std::string item = body.value("item", "");
    if (!item.empty() && type == "add") history.log(item);
    res.set_content(R"({"ok":true})", "application/json");
  });

  svr.Get("/suggest", [&](const httplib::Request& req, httplib::Response& res) {
    std::vector<std::string> currentList;
    if (req.has_param("list")) currentList = splitCsv(req.get_param_value("list"));

    json suggestions = json::array();
    auto ranked = history.scored();
    int count = 0;
    for (const auto& [item, score] : ranked) {
      if (count >= 4) break;
      if (std::find(currentList.begin(), currentList.end(), item) != currentList.end()) continue;
      json s;
      s["item"] = item;
      s["reason"] = "Frequently bought, based on your history";
      suggestions.push_back(s);
      count++;
    }

    time_t t = time(nullptr);
    tm* lt = localtime(&t);
    std::string monthKey = std::to_string(lt->tm_mon + 1);
    if (dict.seasonal.contains(monthKey)) {
      for (const auto& s : dict.seasonal[monthKey]) {
        if (count >= 6) break;
        suggestions.push_back(s);
        count++;
      }
    }

    for (const auto& item : currentList) {
      if (dict.substitutes.contains(item)) {
        for (const auto& sub : dict.substitutes[item]) {
          if (count >= 8) break;
          json s;
          s["item"] = sub.get<std::string>();
          s["reason"] = "Substitute for " + item;
          suggestions.push_back(s);
          count++;
        }
      }
    }

    json out;
    out["suggestions"] = suggestions;
    res.set_content(out.dump(), "application/json");
  });

  svr.Get("/search", [&](const httplib::Request& req, httplib::Response& res) {
    std::string item = toLower(req.get_param_value("item"));
    std::string brand = toLower(req.get_param_value("brand"));
    std::string size = toLower(req.get_param_value("size"));
    bool hasMin = req.has_param("price_min") && !req.get_param_value("price_min").empty();
    bool hasMax = req.has_param("price_max") && !req.get_param_value("price_max").empty();
    double priceMin = hasMin ? std::stod(req.get_param_value("price_min")) : 0.0;
    double priceMax = hasMax ? std::stod(req.get_param_value("price_max")) : 1e18;

    json results = json::array();
    for (const auto& p : dict.catalog) {
      std::string pItem = toLower(p.value("item", ""));
      std::string pBrand = toLower(p.value("brand", ""));
      std::string pSize = toLower(p.value("size", ""));
      double price = p.value("price", 0.0);

      if (!item.empty() && pItem.find(item) == std::string::npos) continue;
      if (!brand.empty() && pBrand.find(brand) == std::string::npos) continue;
      if (!size.empty() && pSize.find(size) == std::string::npos) continue;
      if (price < priceMin || price > priceMax) continue;

      json r;
      r["name"] = p.value("name", "");
      r["price"] = price;
      r["brand"] = p.value("brand", "");
      r["size"] = p.value("size", "");
      results.push_back(r);
    }
    json out;
    out["results"] = results;
    res.set_content(out.dump(), "application/json");
  });

  svr.Get("/health", [](const httplib::Request&, httplib::Response& res) {
    res.set_content(R"({"status":"ok"})", "application/json");
  });

  std::cout << "Voice Shopping Assistant server listening on :" << port << "\n";
  svr.listen("0.0.0.0", port);
  return 0;
}
