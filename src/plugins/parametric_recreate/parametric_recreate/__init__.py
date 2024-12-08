"""
This is where the implementation of the plugin code goes.
The parametric_recreate-class is imported from both run_plugin.py and run_debug.py
"""
import sys
import logging
from webgme_bindings import PluginBase

# Setup a logger
logger = logging.getLogger('parametric_recreate')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)  # By default it logs to stderr..
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class parametric_recreate(PluginBase):
  def main(self):
        active_node = self.active_node
        core = self.core
        logger = self.logger
        
        META = self.META
        config = self.get_current_config()
        parametric_example = self.get_file(config['file'])
        
        #parametric_example = self.get_file('db99f8792399e265c50a05c10646c141a6183de9')
        self.recreate(parametric_example)
        
        
        
        
        # Containers for collected information
        constraints = {}
        parameters = []
        connections = {}

        def at_node(node):
            meta_node = core.get_base_type(node)
            name = core.get_attribute(node, 'name')
            meta_type = core.get_attribute(meta_node, 'name') if meta_node else 'undefined'

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
                connections[name] = {'variable_type': variable_type, 'src': src, 'dst': dst}

        self.util.traverse(active_node, at_node)

        # Generate output
        output = self.generate_output(constraints, parameters, connections)
        logger.info(output)
        
        
        
        #artifact_hash = self.add_artifact('ParametricExample', {'ParametricExample.txt': output})
        #logger.info('The artifact is stored under hash: {0}'.format(artifact_hash))
        
        
  def generate_output(self, constraints, parameters, connections):
        logger = self.logger
        core = self.core
        output = "package 'ParametricDiagrams' {\n"

        # Part definitions
        output += "\tpart def Constraint{\n\t\tattribute equation : String;\n\t\tpart def Variable;\n\t}\n"
        output += "\tpart def Parameter;\n"
        output += "\tpart def Connection{\n\t\tattribute variable_type : String;\n\t}\n\n"

        # Constraints
        for name, data in constraints.items():
            output += f"\tpart {name} : Constraint {{\n"
            output += f"\t\tattribute equation = \"{data['equation']}\";\n"
            for var in data['variables']:
                output += f"\t\tpart {var} : Variable;\n"
            output += "\t}\n\n"

        # Parameters
        for param in parameters:
            output += f"\tpart {param} : Parameter;\n"
        output += "\n"

        # Connections
        for name, data in connections.items():
                output += f"\tpart {name} : Connection {{\n"
                output += f"\t\tattribute variable_type = \"{data['variable_type']}\";\n"

                src_node = core.load_by_path(self.root_node, data['src'])
                dst_node = core.load_by_path(self.root_node, data['dst'])

                src_str = self.get_node_reference(core, src_node)
                dst_str = self.get_node_reference(core, dst_node)

                output += f"\t\tconnect {src_str} to {dst_str};\n"
                output += "\t}\n"



        output += "}\n"
        return output
      
      
  def get_node_reference(self, core, node):
      meta_type = core.get_meta_type(node)
      node_name = core.get_attribute(node, 'name')

      if core.get_attribute(meta_type, 'name') == 'Parameter':
          return f"Parameter.{node_name}"
      else:
          parent = core.get_parent(node)
          parent_name = core.get_attribute(parent, 'name')
          return f"Constraint.{parent_name}.{node_name}"
  def recreate(self, input_string):
      import re
      core = self.core
      root_node = self.active_node
      META = self.META
      logger = self.logger

      constraints = re.findall(r'part (\w+) : Constraint {\n\t\tattribute equation = "(.*?)";\n(.*?)\n\t}', input_string, re.DOTALL)
      parameters = re.findall(r'part (\w+) : Parameter;', input_string)
      connections = re.findall(r'part (\w+) : Connection {\n\t\tattribute variable_type = "(.*?)";\n\t\tconnect (.*?) to (.*?);\n\t}', input_string)

      constraint_nodes = {}
      for name, equation, variables in constraints:
          constraint_node = core.create_node({'parent': root_node, 'base': META['Constraint']})
          core.set_attribute(constraint_node, 'name', name)
          core.set_attribute(constraint_node, 'equation', equation)
          constraint_nodes[name] = constraint_node
            
          for var in re.findall(r'part (\w+) : Variable;', variables):
              var_node = core.create_node({'parent': constraint_node, 'base': META['Variable']})
              core.set_attribute(var_node, 'name', var)

      parameter_nodes = {}
      for param in parameters:
          param_node = core.create_node({'parent': root_node, 'base': META['Parameter']})
          core.set_attribute(param_node, 'name', param)
          parameter_nodes[param] = param_node

      for name, var_type, src, dst in connections:
          conn_node = core.create_node({'parent': root_node,'base': META['Connection']})
          core.set_attribute(conn_node, 'name', name)
          core.set_attribute(conn_node, 'variable_type', var_type)
            
          src_parts = src.split('.')
          dst_parts = dst.split('.')
            
          if src_parts[0] == 'Parameter':
              src_node = parameter_nodes[src_parts[1]]
          else:
              src_node = next(node for node in core.load_children(constraint_nodes[src_parts[1]]) if core.get_attribute(node, 'name') == src_parts[2])
            
          if dst_parts[0] == 'Parameter':
              dst_node = parameter_nodes[dst_parts[1]]
          else:
              dst_node = next(node for node in core.load_children(constraint_nodes[dst_parts[1]]) if core.get_attribute(node, 'name') == dst_parts[2])
            
          core.set_pointer(conn_node, 'src', src_node)
          core.set_pointer(conn_node, 'dst', dst_node)

      self.util.save(self.root_node, self.commit_hash, branch_name='master',msg='parametric_recreation')
      logger.info('Parametric Diagram created successfully.')

