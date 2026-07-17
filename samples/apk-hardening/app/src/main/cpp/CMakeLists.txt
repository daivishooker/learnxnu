cmake_minimum_required(VERSION 3.22.1)
project(native_guard)

add_library(native-guard SHARED native-guard.cpp)

find_library(log-lib log)
target_link_libraries(native-guard ${log-lib})

# Release 构建剥离符号，抬静态分析成本
if(CMAKE_BUILD_TYPE STREQUAL "Release")
  target_link_options(native-guard PRIVATE "-Wl,--strip-all")
endif()
