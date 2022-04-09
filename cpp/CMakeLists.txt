cmake_minimum_required(VERSION 3.10)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

project(place2022_cpp VERSION 1.0)

set(RUNTIME_OUTPUT_DIRECTORY ${PROJECT_SOURCE_DIR}/bin)

add_executable(place2022_cpp ${place2022_cpp_SOURCES})

# Library includes
add_subdirectory(${PROJECT_SOURCE_DIR}/lib/tqdm.cpp)
include_directories(${TQDM_INCLUDE_DIR})

# Main source includes
include_directories(${PROJECT_SOURCE_DIR}/inc/)
target_sources(place2022_cpp
  PRIVATE
    ${PROJECT_SOURCE_DIR}/src/main.cpp
  )
