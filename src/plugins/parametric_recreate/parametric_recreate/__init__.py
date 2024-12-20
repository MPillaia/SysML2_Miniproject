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

        # load file
        META = self.META
        config = self.get_current_config()
        parametric_example = self.get_file(config['file'])
        
        
        self.recreate(parametric_example)
        
  def recreate(self, input_string):
      import re

      # key vars
      core = self.core
      root_node = self.active_node
      META = self.META
      logger = self.logger

      # regex for each node type
      constraints = re.findall(r'part (\w+) : Constraint {\n\t\tattribute equation = "(.*?)";\n(.*?)\n\t}', input_string, re.DOTALL)
      parameters = re.findall(r'part (\w+) : Parameter;', input_string)
      connections = re.findall(r'part (\w+) : Connection {\n\t\tattribute variable_type = "(.*?)";\n\t\tconnect (.*?) to (.*?);\n\t}', input_string)

      constraint_nodes = {}
      for name, equation, variables in constraints: # create constraints
          constraint_node = core.create_node({'parent': root_node, 'base': META['Constraint']})
          core.set_attribute(constraint_node, 'name', name)
          core.set_attribute(constraint_node, 'equation', equation)
          constraint_nodes[name] = constraint_node
            
          for var in re.findall(r'part (\w+) : Variable;', variables):
              var_node = core.create_node({'parent': constraint_node, 'base': META['Variable']})
              core.set_attribute(var_node, 'name', var)

      parameter_nodes = {}
      for param in parameters: # create parameter
          param_node = core.create_node({'parent': root_node, 'base': META['Parameter']})
          core.set_attribute(param_node, 'name', param)
          parameter_nodes[param] = param_node

      for name, var_type, src, dst in connections: # connections
          conn_node = core.create_node({'parent': root_node,'base': META['Connection']})
          core.set_attribute(conn_node, 'name', name)
          core.set_attribute(conn_node, 'variable_type', var_type)
            
          src_parts = src.split('.')
          dst_parts = dst.split('.')
            
          if src_parts[0] == 'Parameter':
              # if its a parameter, simply key by name
              src_node = parameter_nodes[src_parts[1]]
          else:
              # if its a constraint, key into constraints, load children, and get correct variable
              src_node = next(node for node in core.load_children(constraint_nodes[src_parts[1]]) if core.get_attribute(node, 'name') == src_parts[2])
            
          if dst_parts[0] == 'Parameter':
              # if its a parameter, simply key by name
              dst_node = parameter_nodes[dst_parts[1]]
          else:
              # if its a constraint, key into constraints, load children, and get correct variable
              dst_node = next(node for node in core.load_children(constraint_nodes[dst_parts[1]]) if core.get_attribute(node, 'name') == dst_parts[2])
            
          core.set_pointer(conn_node, 'src', src_node)
          core.set_pointer(conn_node, 'dst', dst_node)

      self.util.save(self.root_node, self.commit_hash, branch_name='master',msg='parametric_recreation')

