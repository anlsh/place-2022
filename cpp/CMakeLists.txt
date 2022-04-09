cmake_minimum_required(VERSION 3.10)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

project(place2022_cpp VERSION 1.0)

# Library includes
add_subdirectory(lib/tqdm)
include_directories(${TQDM_INCLUDE_DIR})

# Main source includes
include_directories(${PROJECT_SOURCE_DIR}/inc/)
include_directories(${PROJECT_SOURCE_DIR}/src/)

add_executable(place2022_cpp main.cpp)
