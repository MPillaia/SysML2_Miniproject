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
        nodes = {}
        connections = {}

        def at_node(node):
            meta_node = core.get_base_type(node)
            name = core.get_attribute(node, 'name')
            meta_type = core.get_attribute(meta_node, 'name')

            if meta_type in ['FunctionalRequirement', 'PerformanceRequirement', 'InterfaceRequirement', 'DesignConstraint', 'PhysicalRequirement', 'TestCase']:
                description = core.get_attribute(node, 'description')
                nodes[name] = {'type': meta_type, 'description': description}
            elif meta_type in ['RequirementsDiagram', 'FunctionalRequirements', 'NonFunctionalRequirements']:
                nodes[name] = {'type': meta_type}
            elif 'Connection' in meta_type:
                src = core.get_pointer_path(node, 'src')
                dst = core.get_pointer_path(node, 'dst')
                label = core.get_attribute(node, 'label') if 'label' in core.get_attribute_names(node) else None
                connections[name] = {'type': meta_type, 'src': src, 'dst': dst, 'label': label}

        self.util.traverse(active_node, at_node)

        output = self.generate_output(core, nodes, connections)
        logger.info(output)
        #artifact_hash = self.add_artifact('RequirementsExample', {'requirements_recreation.txt': output})
        #logger.info('The artifact is stored under hash: {0}'.format(artifact_hash))

  def generate_output(self, core, nodes, connections):
        output = "package 'RequirementsDiagrams' {\n"

        # Part definitions
        part_defs = [
            "RequirementsDiagram", "FunctionalRequirements", "NonFunctionalRequirements",
            "FunctionalRequirement", "PerformanceRequirement", "InterfaceRequirement",
            "DesignConstraint", "PhysicalRequirement", "TestCase",
            "RequirementsConnection", "FunctionalRequirementConnection",
            "NonFunctionalRequirementConnection", "TestCaseConnection",
            "PerformanceRequirementConnection", "InterfaceRequirementConnection",
            "DesignConstraintConnection", "PhysicalRequirementConnection"
        ]

        for part in part_defs:
            output += f"\tpart def {part}"
            if part in ["FunctionalRequirement", "PerformanceRequirement", "InterfaceRequirement", "DesignConstraint", "PhysicalRequirement", "TestCase"]:
                output += "{\n\t\tattribute description : String;\n\t}"
            elif "Connection" in part and part != "RequirementsConnection" and part != "FunctionalRequirementConnection" and part != "NonFunctionalRequirementConnection":
                output += "{\n\t\tattribute label : String;\n\t}"
            output += ";\n"

        output += "\n"

        # Nodes
        for name, data in nodes.items():
            output += f"\tpart {name} : {data['type']} {{\n"
            if 'description' in data:
                output += f"\t\tattribute description = \"{data['description']}\";\n"
            output += "\t}\n"

        # Connections
        for name, data in connections.items():
            output += f"\tpart {name} : {data['type']} {{\n"
            if data['label']:
                output += f"\t\tattribute label = \"{data['label']}\";\n"
            src = self.get_node_reference(core, core.load_by_path(self.root_node, data['src']))
            dst = self.get_node_reference(core, core.load_by_path(self.root_node, data['dst']))
            output += f"\t\tconnect {src} to {dst};\n"
            output += "\t}\n"

        output += "}\n"
        return output

  def get_node_reference(self, core, node):
        meta_type = core.get_meta_type(node)
        node_name = core.get_attribute(node, 'name')
        parent = core.get_parent(node)
        parent_name = core.get_attribute(parent, 'name') if parent else None
        parent_type = core.get_attribute(core.get_meta_type(parent), 'name') if parent else None

        if parent_type in ['FunctionalRequirements', 'NonFunctionalRequirements', 'RequirementsDiagram']:
            return f"{parent_type}.{parent_name}"
        else:
            return f"{core.get_attribute(meta_type, 'name')}.{node_name}"
  def recreate(self, text_input):
      import re
  
      root_node = self.active_node
      core = self.core
      META = self.META
  
      lines = text_input.split('\n')
      nodes = {}
      connection_nodes = []
      current_node = None
  
      for line in lines:
          line = line.strip()
          if line.startswith('part ') and ' : ' in line:
              parts = line.split(' : ')
              name = parts[0].split(' ')[1]
              type_name = parts[1].split(' ')[0]
  
              current_node = core.create_node({'parent': root_node, 'base': META[type_name]})
              core.set_attribute(current_node, 'name', name)
              
              if 'Connection' in type_name:
                  connection_nodes.append(current_node)
              else:
                  nodes[name] = current_node
  
          elif current_node and line.startswith('attribute '):
              attr_match = re.search(r'attribute (\w+) = "(.*?)"', line)
              if attr_match:
                  attr_name, attr_value = attr_match.groups()
                  core.set_attribute(current_node, attr_name, attr_value)
  
          elif current_node and line.startswith('connect '):
              connect_parts = line.split('connect ')[1].split(' to ')
              src = connect_parts[0].split('.')
              dst = connect_parts[1].rstrip(';').split('.')
  
              src_node = nodes[src[-1]] if len(src) > 1 else nodes[src[0]]
              dst_node = nodes[dst[-1]] if len(dst) > 1 else nodes[dst[0]]
  
              core.set_pointer(current_node, 'src', src_node)
              core.set_pointer(current_node, 'dst', dst_node)
  
          elif line == '}':
              current_node = None
  
      self.util.save(self.root_node, self.commit_hash, branch_name = 'master', msg='requirements_recreation')
  
