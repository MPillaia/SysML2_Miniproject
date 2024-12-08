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
        #self.traverse_diagram()

        #output = self.generate_output()
        #self.logger.info(output)
        #artifact_hash = self.add_artifact('IBDExample', {'IBDExample.txt': output})
        #self.logger.info('The artifact is stored under hash: {0}'.format(artifact_hash))
        

  def traverse_diagram(self):
        def process_node(node, parent=None):

            meta_type = self.core.get_attribute(self.core.get_meta_type(node), 'name')
            name = self.core.get_attribute(node, 'name')
            node_data = {
                'type': meta_type,
                'parent': parent,
                'children': [],
                'ports': [],
                'participants': self.core.get_attribute(node, 'participants') if meta_type in ['Block', 'Constraint'] else None
            }
            if meta_type in ['BlockConnection', 'Dependancy']:
                node_data['src'] = self.core.get_pointer_path(node, 'src')
                node_data['dst'] = self.core.get_pointer_path(node, 'dst')
            if parent:
                
                self.nodes[parent]['children'].append(name)
                
            if meta_type == 'Port' and parent:
                self.nodes[parent]['ports'].append(name)
               
            else:
                
                self.nodes[name] = node_data
            for child in self.core.load_children(node):
                process_node(child, name)

            

        self.util.traverse(self.active_node, process_node)

  def generate_output(self):
        output = "package 'InternalBlockDiagrams' {\n"
        output += self.generate_part_definitions()
        output += self.generate_elements()
        output += "}\n"
        return self.remove_duplicates(output)
        

  def generate_part_definitions(self):
        return """
\tpart def Block {
\t\tattribute participants : String;
\t\tpart def Port;
\t}
\tpart def Constraint {
\t\tattribute participants : String;
\t}
\tpart def BlockConnection;
\tpart def Dependancy;\n
"""

  def generate_elements(self):
    output = ""
    for name, data in self.nodes.items():
        if data['parent'] is None:  # Top-level elements
            if data['type'] == 'Block':
                output += self.generate_block(name, data, 1)
            elif data['type'] == 'Constraint':
                output += self.generate_constraint(name, data, 1)
            elif data['type'] == 'BlockConnection':
                output += self.generate_block_connection(name, data, 1)
            elif data['type'] == 'Dependancy':
                output += self.generate_dependency(name, data, 1)
    return output

  def generate_block(self, name, data, indent):
    output = f"{'	' * indent}part {name} : Block {{\n"
    output += f"{'	' * (indent+1)}attribute participants = \"{data['participants']}\";\n"
    for port in data['ports']:
        output += f"{'	' * (indent+1)}part {port} : Port;\n"
    for child in data['children']:
        child_data = self.nodes[child]
        if child_data['type'] == 'Block':
            output += self.generate_block(child, child_data, indent+1)
        elif child_data['type'] == 'Constraint':
            output += self.generate_constraint(child, child_data, indent+1)
        elif child_data['type'] == 'BlockConnection':
            output += self.generate_block_connection(child, child_data, indent+1)
        elif child_data['type'] == 'Dependancy':
            output += self.generate_dependency(child, child_data, indent+1)
    output += f"{'	' * indent}}}\n\n"
    return output

  def generate_constraint(self, name, data, indent):
    output = f"{'	' * indent}part {name} : Constraint {{\n"
    output += f"{'	' * (indent+1)}attribute participants = \"{data['participants']}\";\n"
    for child in data['children']:
        child_data = self.nodes[child]
        if child_data['type'] == 'Block':
            output += self.generate_block(child, child_data, indent+1)
        elif child_data['type'] == 'Constraint':
            output += self.generate_constraint(child, child_data, indent+1)
        elif child_data['type'] == 'BlockConnection':
            output += self.generate_block_connection(child, child_data, indent+1)
        elif child_data['type'] == 'Dependancy':
            output += self.generate_dependency(child, child_data, indent+1)
    output += f"{'	' * indent}}}\n\n"
    return output

  def generate_block_connection(self, name, data, indent):
    src_node = self.core.load_by_path(self.root_node, data['src'])
    dst_node = self.core.load_by_path(self.root_node, data['dst'])
    src_block = self.core.get_parent(src_node)
    dst_block = self.core.get_parent(dst_node)
    
    src_block_name = self.core.get_attribute(src_block, 'name')
    src_port_name = self.core.get_attribute(src_node, 'name')
    dst_block_name = self.core.get_attribute(dst_block, 'name')
    dst_port_name = self.core.get_attribute(dst_node, 'name')
    
    output = f"{'	' * indent}part {name} : BlockConnection {{\n"
    output += f"{'	' * (indent+1)}connect {src_block_name}.{src_port_name} to {dst_block_name}.{dst_port_name};\n"
    output += f"{'	' * indent}}}\n\n"
    return output

  def generate_dependency(self, name, data, indent):
    src_node = self.core.load_by_path(self.root_node, data['src'])
    dst_node = self.core.load_by_path(self.root_node, data['dst'])
    
    src_name = self.core.get_attribute(src_node, 'name')
    dst_name = self.core.get_attribute(dst_node, 'name')
    
    output = f"{'	' * indent}part {name} : Dependancy {{\n"
    output += f"{'	' * (indent+1)}connect {src_name} to {dst_name};\n"
    output += f"{'	' * indent}}}\n\n"
    return output
  def remove_duplicates(self, output):
    lines = output.split('\n')
    seen = set()
    filtered_lines = []
    stack = []
    current_indent = 0
    skip_until_less_indent = False

    for line in lines:
        stripped_line = line.strip()
        indent = len(line) - len(stripped_line)
        
        if indent <= current_indent:
            skip_until_less_indent = False

        if skip_until_less_indent:
            continue

        if stripped_line.startswith('part') and ':' in stripped_line:
            part_name = stripped_line.split(':')[0].split()[-1]
            part_type = stripped_line.split(':')[1].split()[0]
            if part_name in seen and part_type != 'Port;' and part_type != 'Dependancy':
                skip_until_less_indent = True
                current_indent = indent
            else:
                seen.add(part_name)
                filtered_lines.append(line)
                if stripped_line.endswith('{'):
                    stack.append(indent)
        elif stripped_line == '}':
            if stack and indent == stack[-1]:
                filtered_lines.append(line)
                stack.pop()
        else:
            filtered_lines.append(line)

    return '\n'.join(filtered_lines)
  
  def recreate(self, output_string):
      
      core = self.core
      active_node = self.active_node
      lines = output_string.split('\n')
      stack = [active_node]
      block_connections = []
      dependancies = []
      all_nodes = {}
      self.logger.info("111")
      for line in lines:
          stripped_line = line.strip().rstrip(';')

          if stripped_line == '}':
              if len(stack) > 1:
                  stack.pop()
              continue

          if stripped_line.startswith('part') and ':' in stripped_line:
              parts = stripped_line.split(':')
              node_name = parts[0].split()[1]
              node_type = parts[1].split()[0].strip()

              new_node = core.create_node({'parent': stack[-1], 'base': self.META[node_type]})
              core.set_attribute(new_node, 'name', node_name)
              node_path = core.get_path(new_node)
              all_nodes[node_path] = new_node

              if node_type in ['Block', 'Constraint']:
                  participants = next((l.split('=')[1].strip(' "')[:-2 or None]  for l in lines[lines.index(line)+1:] if 'participants' in l), None)
                  if participants:
                      core.set_attribute(new_node, 'participants', participants)

              if stripped_line.endswith('{'):
                  stack.append(new_node)

          elif stripped_line.startswith('connect'):
              parts = stripped_line.split()
              node_type = core.get_attribute(core.get_meta_type(stack[-1]), 'name')
              self.logger.info(core.get_meta_type(stack[-1]))
              if node_type == 'BlockConnection':
                  block_connections.append((core.get_path(stack[-1]), parts[1], parts[3]))
              elif node_type ==  'Dependancy':
                  dependancies.append((core.get_path(stack[-1]), parts[1], parts[3]))
      self.logger.info("222")
      self.set_connections(core, all_nodes, block_connections, dependancies)
      self.util.save(self.root_node, self.commit_hash, branch_name = 'master', msg = 'zzzzz')

  def set_connections(self, core, all_nodes, block_connections, dependancies):
      for connection_path, src, dst in block_connections:
          connection_node = all_nodes[connection_path]
          src_block_name, src_port_name = src.split('.')
          dst_block_name, dst_port_name = dst.split('.')

          src_block = self.find_node_by_name(core, all_nodes.values(), src_block_name)
          dst_block = self.find_node_by_name(core, all_nodes.values(), dst_block_name)

          if src_block and dst_block:
              src_port = self.find_node_by_name(core, core.load_children(src_block), src_port_name)
              dst_port = self.find_node_by_name(core, core.load_children(dst_block), dst_port_name)

              if src_port and dst_port:
                  core.set_pointer(connection_node, 'src', src_port)
                  core.set_pointer(connection_node, 'dst', dst_port)

      self.logger.info(dependancies)
      for connection_path, src, dst in dependancies:
          connection_node = all_nodes[connection_path]
          src_node = self.find_node_by_name(core, all_nodes.values(), src)
          dst_node = self.find_node_by_name(core, all_nodes.values(), dst)

          if src_node and dst_node:
              core.set_pointer(connection_node, 'src', src_node)
              core.set_pointer(connection_node, 'dst', dst_node)

  def find_node_by_name(self, core, nodes, name):
      for node in nodes:
          if core.get_attribute(node, 'name') == name:
              return node
          children = core.load_children(node)
          found = self.find_node_by_name(core, children, name)
          if found:
              return found
      return None
