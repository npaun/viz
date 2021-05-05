/** This is the dumbest JSON serializer ever.
 *  Hopefully, it's faster than a real one for
 *  our really simple, but performance-sensitive objects
 */
#ifndef sjson_h
#define sjson_h
#include <iomanip>
#include <iostream>
#include <openssl/md5.h>
#include <regex>
#include <sstream>
#include <string>
#include <tuple>
#include <type_traits>
#include <unordered_map>
#include <utility>
#include <vector>

namespace npvis::sjson {
std::string id_tojkey(const std::string &id) {
  unsigned char digest[MD5_DIGEST_LENGTH];
  MD5(reinterpret_cast<const unsigned char *>(id.data()), id.size(), digest);
  std::stringstream sstr;
  for (auto i = 0; i < MD5_DIGEST_LENGTH; i++) {
    sstr << std::setfill('0') << std::setw(2) << std::hex
         << static_cast<int>(digest[i]);
  }
  return sstr.str();
}
template <class T, template <class...> class Template>
struct is_specialization : std::false_type {};

template <template <class...> class Template, class... Args>
struct is_specialization<Template<Args...>, Template> : std::true_type {};

/* For non-peculiar types: just let C++ turn it into a string */
template <typename T, typename Enable = void> struct writer {
  writer(std::stringstream &sstr, T val) { sstr << val; }
};

const std::regex quote_re("\"");

template <> struct writer<std::string> {
  writer(std::stringstream &sstr, const std::string &val) {
    if (val.find('"') != std::string::npos) {
      // We must escape it
      sstr << '"' << std::regex_replace(val, quote_re, "\\\"") << '"';
    } else {
      sstr << '"' << val << '"';
    }
  }
};

template <typename T>
struct writer<T, std::enable_if_t<is_specialization<T, std::vector>{}>> {
  writer(std::stringstream &sstr, T val) {
    if (val.empty()) {
      sstr << "[]";
      return;
    }

    sstr << "[";
    writer<typename T::value_type>(sstr, val[0]);
    for (std::size_t i = 1; i < val.size(); i++) {
      sstr << ", ";
      writer<typename T::value_type>(sstr, val[i]);
    }

    sstr << "]";
  }
};

template <typename T>
struct writer<T, std::enable_if_t<is_specialization<T, std::tuple>{}>> {
  writer(std::stringstream &sstr, T val) {
    sstr << "[";
    std::apply(
        [&sstr](auto h, auto... t) {
          writer<decltype(h)>(sstr, h);
          ((sstr << ", ", writer<decltype(t)>(sstr, t)), ...);
        },
        val);

    sstr << "]";
  }
};

template <typename T>
struct writer<T, std::enable_if<is_specialization<T, std::unordered_map>{}>> {
  writer(std::stringstream &sstr, T val) {
    sstr << "{\n";
    write_kv_map(sstr, true, val);
    sstr << "\n}";
  }
};

/* Useful for dynamically typed objects and for strict maps */
template <typename T>
void write_kv_pair(std::stringstream &sstr, bool first, const std::string &k,
                   T v) {
  if (!first) {
    sstr << ",\n";
  }

  sstr << "    ";
  writer(sstr, k);
  sstr << ": ";
  writer(sstr, v);
}

template <typename V>
void write_kv_map(std::stringstream &sstr, bool first,
                  const std::unordered_map<std::string, V> &source) {
  for (const auto &[k, v] : source) {
    write_kv_pair(sstr, first, k, v);
    first = false;
  }
}

struct object {
  object() { sstr << "{\n"; }

  template <typename T> object &add(const std::string &k, T v) {
    write_kv_pair(sstr, first, k, v);
    first = false;
    return *this;
  }

  object &add_str(const std::string &k, int v) {
    return add(k, std::to_string(v));
  }

  template <typename Elm,
            std::enable_if_t<std::is_arithmetic<Elm>::value, int> = 0>
  object &add_str(const std::string &k, const std::vector<Elm> &v) {
    // Potential optimization later
    std::vector<std::string> strV;
    strV.reserve(v.size());
    for (const auto &elm : v) {
      strV.push_back(std::to_string(elm));
    }

    return add(k, strV);
  }

  object &add_jkey(const std::string &k, const std::string &v) {
    return add(k, id_tojkey(v));
  }

  std::string str() {
    sstr << "\n}";
    return sstr.str();
  }

  template <typename V>
  object &extend(const std::unordered_map<std::string, V> &source) {
    write_kv_map(sstr, first, source);
    first = false;
    return *this;
  }

  std::stringstream sstr;
  bool first = true;
};

} // namespace npvis::sjson

/*int main(int argc, char* argv[]) {
    std::stringstream sstr;
    std::unordered_map<std::string, std::string> m;
    m["dog"] = "fifteen";
    m["cow"] = "seven";
    npvis::sjson::object o;
    o.extend(m);
    o.add("sheep", 15);
    std::vector v = {1,3,4};
    o.add("pink", v);
    std::cout << o.str() << std::endl;
}*/
#endif
