"""
This is where the implementation of the plugin code goes.
The IBD_recreate-class is imported from both run_plugin.py and run_debug.py
"""
import sys
import logging
from webgme_bindings import PluginBase

# Setup a logger
logger = logging.getLogger('IBD_recreate')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)  # By default it logs to stderr..
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class IBD_recreate(PluginBase):
  def main(self):

        self.active_node = self.active_node
        self.core = self.core
        self.logger = self.logger
        self.nodes = {}
        
        self.namespace = None
        META = self.META
        config = self.get_current_config()
        IBD_example = self.get_file(config['file'])
        self.recreate(IBD_example)

        
  def recreate(self, output_string):
      
      core = self.core
      active_node = self.active_node
      lines = output_string.split('\n')
      stack = [active_node]
      block_connections = []
      dependancies = []
      all_nodes = {}
      self.logger.info("111")
      for line in lines: # line by line
          stripped_line = line.strip().rstrip(';')

          if stripped_line == '}': # go up one composition level, to previous parent
              if len(stack) > 1:
                  stack.pop()
              continue

          if stripped_line.startswith('part') and ':' in stripped_line: # part creation
              parts = stripped_line.split(':')
              node_name = parts[0].split()[1]
              node_type = parts[1].split()[0].strip()


              # create node
              new_node = core.create_node({'parent': stack[-1], 'base': self.META[node_type]})
              core.set_attribute(new_node, 'name', node_name)
              node_path = core.get_path(new_node)
              all_nodes[node_path] = new_node

              if node_type in ['Block', 'Constraint']: # get participant from next line
                  participants = next((l.split('=')[1].strip(' "')[:-2 or None]  for l in lines[lines.index(line)+1:] if 'participants' in l), None)
                  if participants:
                      core.set_attribute(new_node, 'participants', participants)

              if stripped_line.endswith('{'): # new parent, composition level
                  stack.append(new_node)

          elif stripped_line.startswith('connect'):
              parts = stripped_line.split()
              node_type = core.get_attribute(core.get_meta_type(stack[-1]), 'name')
              # get node type of connection node
              self.logger.info(core.get_meta_type(stack[-1]))

              # seperate list for BlockConnection and Dependancy, since need to create BlockConnection first
              if node_type == 'BlockConnection':
                  block_connections.append((core.get_path(stack[-1]), parts[1], parts[3]))
              elif node_type ==  'Dependancy':
                  dependancies.append((core.get_path(stack[-1]), parts[1], parts[3]))
      self.logger.info("222")
      # set connections after nodes created
      self.set_connections(core, all_nodes, block_connections, dependancies)
      self.util.save(self.root_node, self.commit_hash, branch_name = 'master', msg = 'zzzzz')

  def set_connections(self, core, all_nodes, block_connections, dependancies):
      for connection_path, src, dst in block_connections: # block connections first
          connection_node = all_nodes[connection_path]
          src_block_name, src_port_name = src.split('.')
          dst_block_name, dst_port_name = dst.split('.')

          # find Block
          src_block = self.find_node_by_name(core, all_nodes.values(), src_block_name)
          dst_block = self.find_node_by_name(core, all_nodes.values(), dst_block_name)

          if src_block and dst_block: # find port
              src_port = self.find_node_by_name(core, core.load_children(src_block), src_port_name)
              dst_port = self.find_node_by_name(core, core.load_children(dst_block), dst_port_name)

              if src_port and dst_port:
                  core.set_pointer(connection_node, 'src', src_port)
                  core.set_pointer(connection_node, 'dst', dst_port)

      self.logger.info(dependancies)
      for connection_path, src, dst in dependancies: # dependancy
          # can just find each part
          connection_node = all_nodes[connection_path]
          src_node = self.find_node_by_name(core, all_nodes.values(), src)
          dst_node = self.find_node_by_name(core, all_nodes.values(), dst)

          if src_node and dst_node:
              core.set_pointer(connection_node, 'src', src_node)
              core.set_pointer(connection_node, 'dst', dst_node)

  def find_node_by_name(self, core, nodes, name):
      # traversal of nodes and children
      for node in nodes:
          if core.get_attribute(node, 'name') == name:
              return node
          children = core.load_children(node)
          found = self.find_node_by_name(core, children, name)
          if found:
              return found
      return None
