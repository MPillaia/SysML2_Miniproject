"""
This is where the implementation of the plugin code goes.
The parametric_write-class is imported from both run_plugin.py and run_debug.py
"""
import sys
import logging
from webgme_bindings import PluginBase

# Setup a logger
logger = logging.getLogger('parametric_write')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)  # By default it logs to stderr..
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class parametric_write(PluginBase):
    def main(self):
        active_node = self.active_node
        core = self.core
        logger = self.logger
        
        constraints = {}
        parameters = []
        connections = []

        # Function to create log of each note
        def at_node(node):
            # get meta node type
            meta_node = core.get_base_type(node)
            name = core.get_attribute(node, 'name')
            meta_type = core.get_attribute(meta_node, 'name') if meta_node else 'undefined'

            # get key attributes for each type
            if meta_type == 'Constraint':
                equation = core.get_attribute(node, 'equation')
                variables = [core.get_attribute(child, 'name') for child in core.load_children(node)]
                constraints[name] = {'equation': equation, 'variables': variables}
            elif meta_type == 'Parameter':
                parameters.append(name)
            elif meta_type == 'Connection':
                variable_type = core.get_attribute(node, 'variable_type')
                src = core.get_pointer_path(node, 'src')
                dst = core.get_pointer_path(node, 'dst')
                connections.append({
                    'name': name,
                    'variable_type': variable_type,
                    'src': src,
                    'dst': dst
                })

        # traversal
        self.util.traverse(active_node, at_node)

        output = self.generate_output(constraints, parameters, connections)
        logger.info(output)
        
        with open("/usr/app/src/parametric_output.txt", "w") as text_file:
            text_file.write(output)

    def generate_output(self, constraints, parameters, connections):
        logger = self.logger
        core = self.core

        # templating
        output = "package 'ParametricDiagrams' {\n"

        output += "\tpart def Constraint{\n\t\tattribute equation : String;\n\t\tpart def Variable;\n\t}\n"
        output += "\tpart def Parameter;\n"
        output += "\tpart def Connection{\n\t\tattribute variable_type : String;\n\t}\n\n"

        for name, data in constraints.items(): # set up constraints
            output += f"\tpart {name} : Constraint {{\n"
            output += f"\t\tattribute equation = \"{data['equation']}\";\n"
            for var in data['variables']:
                output += f"\t\tpart {var} : Variable;\n"
            output += "\t}\n\n"

        for param in parameters: # set up parameters
            output += f"\tpart {param} : Parameter;\n"
        output += "\n"

        for conn in connections: # set up connections
            output += f"\tpart {conn['name']} : Connection {{\n"
            output += f"\t\tattribute variable_type = \"{conn['variable_type']}\";\n"

            # load src and dst, get proper format for 'connect' keyword
            src_node = core.load_by_path(self.root_node, conn['src'])
            dst_node = core.load_by_path(self.root_node, conn['dst'])

            src_str = self.get_node_reference(core, src_node)
            dst_str = self.get_node_reference(core, dst_node)

            output += f"\t\tconnect {src_str} to {dst_str};\n"
            output += "\t}\n"

        output += "}\n"
        return output
      
    def get_node_reference(self, core, node):
        # get type and name
        meta_type = core.get_meta_type(node)
        node_name = core.get_attribute(node, 'name')

        # set up proper 'connect' format
        if core.get_attribute(meta_type, 'name') == 'Parameter':
            return f"Parameter.{node_name}"
        else:
            parent = core.get_parent(node)
            parent_name = core.get_attribute(parent, 'name')
            return f"Constraint.{parent_name}.{node_name}"