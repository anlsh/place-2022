cmake_minimum_required(VERSION 3.10)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

project(place2022_cpp VERSION 1.0)

set(RUNTIME_OUTPUT_DIRECTORY ${PROJECT_SOURCE_DIR}/bin)

add_executable(place2022_cpp ${place2022_cpp_SOURCES})

# Library includes
# TODO I wanted to use ${TQDM_INCLUDE_DIR} from the subproject, but that variable
# ends up empty so...
add_subdirectory(${PROJECT_SOURCE_DIR}/lib/tqdm.cpp)
target_include_directories(place2022_cpp PUBLIC ${PROJECT_SOURCE_DIR}/lib/tqdm.cpp/include)

# https://stackoverflow.com/questions/30980383/cmake-compile-options-for-libpng
# FindPNG()
find_package(PNG REQUIRED)
add_definitions(${PNG_DEFINITIONS})
target_include_directories(place2022_cpp PUBLIC ${PNG_INCLUDE_DIRS})
target_link_libraries(place2022_cpp ${PNG_LIBRARIES})

# Main source includes
include_directories(${PROJECT_SOURCE_DIR}/inc/)
# target_link_libraries(place2022_cpp PRIVATE tqdm)
target_sources(place2022_cpp
  PUBLIC
    ${PROJECT_SOURCE_DIR}/src/main.cpp
  )
