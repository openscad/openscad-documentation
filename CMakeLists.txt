cmake_minimum_required(VERSION 3.16)

find_package(Python3 COMPONENTS Interpreter)

set(Doc_Script ${CMAKE_CURRENT_SOURCE_DIR}/scripts/offline-doc-generator.py)
    
execute_process(COMMAND ${Python3_EXECUTABLE} -m pip install -r ${CMAKE_CURRENT_SOURCE_DIR}/scripts/requirements.txt)

add_custom_target(doc ALL COMMAND ${Python3_EXECUTABLE} ${Doc_Script})
