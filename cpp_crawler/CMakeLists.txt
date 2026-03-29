cmake_minimum_required(VERSION 3.14)

project(devnavigator LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(SQLite3 REQUIRED)
find_package(CURL REQUIRED)

add_executable(devnavigator
    src/main.cpp
    src/crawler.cpp
    src/parser.cpp
    src/email_sender.cpp
)

target_include_directories(devnavigator PRIVATE include)
target_link_libraries(devnavigator SQLite::SQLite3 CURL::libcurl)
