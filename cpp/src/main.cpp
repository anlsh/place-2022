#include <iostream>
#include "tqdm/tqdm.h"
#include "png.h"

int main() {
    std::cout << "Foobar" << std::endl;
    for (int i : tqdm::range(30000000));
}
