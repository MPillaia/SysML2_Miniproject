"""
This is where the implementation of the plugin code goes.
The requirements_write-class is imported from both run_plugin.py and run_debug.py
"""
import sys
import logging
from webgme_bindings import PluginBase

# Setup a logger
logger = logging.getLogger('requirements_write')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)  # By default it logs to stderr..
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class requirements_write(PluginBase):
    def main(self):
        active_node = self.active_node
        core = self.core
        logger = self.logger

        nodes = {}
        connections = []

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
                connections.append({'name': name, 'type': meta_type, 'src': src, 'dst': dst, 'label': label})

        self.util.traverse(active_node, at_node)

        output = self.generate_output(core, nodes, connections)
        logger.info(output)
        with open("/usr/app/src/requirements_output.txt", "w") as text_file:
            text_file.write(output)

    def generate_output(self, core, nodes, connections):
        output = "package 'RequirementsDiagrams' {\n"

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

        for name, data in nodes.items():
            output += f"\tpart {name} : {data['type']} {{\n"
            if 'description' in data:
                output += f"\t\tattribute description = \"{data['description']}\";\n"
            output += "\t}\n"

        for data in connections:
            output += f"\tpart {data['name']} : {data['type']} {{\n"
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