"""
This is where the implementation of the plugin code goes.
The requirements_recreate-class is imported from both run_plugin.py and run_debug.py
"""
import sys
import logging
from webgme_bindings import PluginBase

# Setup a logger
logger = logging.getLogger('requirements_recreate')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)  # By default it logs to stderr..
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class requirements_recreate(PluginBase):
  def main(self):
        active_node = self.active_node
        core = self.core
        logger = self.logger
        self.namespace = None
        META = self.META
        config = self.get_current_config()
        requirements_example = self.get_file(config['file'])
        self.recreate(requirements_example)



  def recreate(self, text_input):
      import re
  
      root_node = self.active_node
      core = self.core
      META = self.META
  
      lines = text_input.split('\n')
      nodes = {}
      connection_nodes = []
      current_node = None

      # sequential processing
      for line in lines:
          line = line.strip()
          if line.startswith('part ') and ' : ' in line: # part creation
              # part name, time
              parts = line.split(' : ')
              name = parts[0].split(' ')[1]
              type_name = parts[1].split(' ')[0]

              # create node
              current_node = core.create_node({'parent': root_node, 'base': META[type_name]})
              core.set_attribute(current_node, 'name', name)

              # connection or requirements node
              if 'Connection' in type_name:
                  connection_nodes.append(current_node)
              else:
                  nodes[name] = current_node
  
          elif current_node and line.startswith('attribute '): # if node we are processing has an attribute
              attr_match = re.search(r'attribute (\w+) = "(.*?)"', line)
              if attr_match:
                  attr_name, attr_value = attr_match.groups()
                  core.set_attribute(current_node, attr_name, attr_value)

          # if node we are processing is a connection
          elif current_node and line.startswith('connect '):
              connect_parts = line.split('connect ')[1].split(' to ')
              src = connect_parts[0].split('.')
              dst = connect_parts[1].rstrip(';').split('.')

              # was throwing error with old write format
              src_node = nodes[src[-1]] if len(src) > 1 else nodes[src[0]]
              dst_node = nodes[dst[-1]] if len(dst) > 1 else nodes[dst[0]]
  
              core.set_pointer(current_node, 'src', src_node)
              core.set_pointer(current_node, 'dst', dst_node)
  
          elif line == '}': # finished processing node
              current_node = None
  
      self.util.save(self.root_node, self.commit_hash, branch_name = 'master', msg='requirements_recreation')
  
