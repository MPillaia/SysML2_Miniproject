# SysML2
This repository allows for the creation of a SysML2 design studio. The creation of three diagram types is supported: parametric, requirements, and internal block. For these diagrams, plugins to write them to file and recreate from file have also been included.

## Initialization
The easiest way to start using this project is to fork it in git. Alternatively, you can create your empty repository, copy the content and just rename all instances of 'WDeStuP' to your liking. Assuming you fork, you can start-up following this few simple steps:
- install [Docker-Desktop](https://www.docker.com/products/docker-desktop)
- clone the repository
- edit the '.env' file so that the BASE_DIR variable points to the main repository directory
- `docker-compose up -d`
- connect to your server at http://localhost:8888

## Naming Requirements
To support consistent diagram write and recreation, each diagram has a few naming uniqueness requirements.

- Parametric Diagram: Parameters and Constraints should have unique names within their node type. Variables and connections do not need to have unique names.
- Requirements Diagram: All Requirements and TestCase nodes should have unique names. Connection nodes do not have to have unique names.
- Internal Block Diagrams: All nodes except Ports should have unique names. 

## Future Work
We aim to implement decorators to provide a cleaner modeling experience and to follow the SysML visual syntax.