#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Ontology Engineering Group
        http://www.oeg-upm.net/
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Copyright (C) 2017 Ontology Engineering Group.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Geographic Information System Worker is licensed under a
  Creative Commons Attribution-NC 4.0 International License.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
"""

import os
import sys
import utils
import settings
import defusedxml.ElementTree

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')

__author__ = "Alejandro F. Carrera"
__copyright__ = "Copyright 2017 © GeoLinkeddata Platform"
__credits__ = ["Alejandro F. Carrera", "Oscar Corcho"]
__license__ = "Creative Commons Attribution-Noncommercial license"
__maintainer__ = "Alejandro F. Carrera"
__email__ = "alejfcarrera@mail.ru"


##########################################################################


config = settings.Config()


##########################################################################


class WorkerXML(object):
    """ This constructor creates only an instance of a
        Object with some features and methods for XML files.
        These files are important because are the format
        for GeoKettle jobs and transformations.

    Returns:
        class: XML Worker

    """

    def get_node_folder(self, path, node_path):
        """ This function allows you to parse and verify if
            a path is or not a XML special variable.

        Args:
            path: file's path
            node_path: node's value path

        Returns:
             tuple: verified path and flag of conversion

        """

        # Get file's path without file
        __file_path = os.path.dirname(path)

        # Generate a full copy of node path
        __node_path = str(node_path)

        # Save flag to determine if a path is a variable
        __node_flag = False

        # Iterate over XML variables
        for folder in config.xml_special_paths:

            # Check if path is a variable
            if __node_path.startswith(folder):
                __node_path = __node_path.replace(
                    folder, __file_path
                )
                __node_flag = True
                break

        # Check if folder is the same of file's path
        if not __node_flag:
            __node_flag = os.path.dirname(
                __node_path
            ).startswith(__file_path)

        # Get folder without file
        return __node_path, __node_flag

    def check_issues(self, path):
        """ This function allows to check any issue from
            a XML file and also vulnerabilities.

        Args:
            path (string): file's path

        Returns:
            class: XML ElementTree or None if something
                went wrong

        """

        try:

            # defusedxml will only be used for check XML problems
            # because this library is slower than python library
            # https://docs.python.org/2/library/xml.html#xml-vulnerabilities
            return defusedxml.ElementTree.parse(path)

        except Exception:
            return None

    def check_steps(self, xml_tree):
        """ This function allows to check if the
            included steps on the XML file are or
            not allowed.

        Args:
            xml_tree (ElementTree): tree to review

        Returns:
            tuple: non and valid steps

        """

        # Structure to save non valid steps
        __no_steps = []
        __valid_steps = set()

        # Get steps from XML file
        __steps = xml_tree.findall('step')

        # Check if any step exist
        if __steps is None:
            return __no_steps, __valid_steps

        # Iterate over steps
        for __step in __steps:

            # Get type if it exists
            __type_node = __step.find('type')

            # Get value of node
            if __type_node is not None:

                # Value of node
                __type = __type_node.text

                # Check if there is config
                # All allowed
                if not len(config.xml_allowed_steps):
                    __valid_steps.add(__type)

                else:

                    # Check type is good
                    if __type not in config.xml_allowed_steps:
                        __no_steps.append(__type)
                    else:
                        __valid_steps.add(__type)

        return __no_steps, list(__valid_steps)

    def check_entries(self, xml_tree):
        """ This function allows to check if the
            included entries on the XML file are or
            not allowed.

        Args:
            xml_tree (ElementTree): tree to review

        Returns:
            tuple: non and valid entries

        """

        # Structure to save non valid entries
        __no_entries = []
        __valid_entries = set()

        # Get entries from XML file
        __entries = xml_tree.findall('entry')

        # Check if any step exist
        if __entries is None:
            return __no_entries, __valid_entries

        # Iterate over entries
        for __entry in __entries:

            # Get type if it exists
            __type_node = __entry.find('type')

            # Get value of node
            if __type_node is not None:

                # Value of node
                __type = __type_node.text

                # Check if there is config
                # All allowed
                if not len(config.xml_allowed_entries):
                    __valid_entries.add(__type)

                else:

                    # Check type is good
                    if __type not in config.xml_allowed_entries:
                        __no_entries.append(__type)
                    else:
                        __valid_entries.add(__type)

        return __no_entries, list(__valid_entries)

    def check_paths(self, path, xml_tree, node_name):
        """ This function allows to check if the
            included paths on the XML file are
            or not allowed.

        Args:
            path (string): file's path
            xml_tree (ElementTree): tree to review
            node_name (string): name of node to review

        Returns:
            triple: steps with non valid paths,
                non and valid paths

        """

        # Structure to save non valid steps
        __no_nodes = []
        __no_folders = []
        __valid_folders = set()

        # Get all nodes
        __nodes = xml_tree.findall(node_name)

        # Check if any node exist
        if __nodes is None:
            return __no_nodes, __no_folders, __valid_folders

        # Iterate over nodes
        for __node in __nodes:

            # Check kind of step and children nodes
            __node_f = __node.find('filename')
            if __node_f is None:
                __node_f = __node.find('file')
            if __node_f is None:
                continue

            # Get filename node
            if __node_f.tag == 'filename':

                # Check node is valid
                if __node_f.text == '':
                    __no_nodes.append(__node.find('type').text)
                    continue

                # Get node value
                __node_f = __node_f.text

            # Get file node
            elif __node_f.tag == 'file':

                # Get name node from node's children
                __node_n = __node_f.find('name')

                # Get extension node from node's children
                __node_e = __node_f.find('extention')

                # Check if plugin has other field
                if __node_e is None:
                    __node_e = __node_f.find('extension')

                # Check node is valid
                if __node_n is None or __node_e is None:
                    __no_nodes.append(__node.find('type').text)
                    continue

                # Check node is valid
                if __node_n.text == '' or __node_e.text == '':
                    __no_nodes.append(__node.find('type').text)
                    continue

                # Create path from values
                __node_f = __node_n.text + '.' + __node_e.text

            # Verify directory from value
            __node_f, __folder_flag = self.get_node_folder(path, __node_f)

            # Get directory from value
            __folder = os.path.dirname(__node_f)

            # Check if folder was a variable
            if __folder_flag:
                __valid_folders.add(__node_f)

            else:

                # Check if there is config
                if not len(config.xml_allowed_paths):
                    __valid_folders.add(__node_f)

                else:

                    # Check folder is good
                    if __folder not in config.xml_allowed_paths:
                        __no_folders.append(__node_f)

                    else:
                        __valid_folders.add(__node_f)

        return __no_nodes, __no_folders, list(__valid_folders)

    def check_srs(self, xml_tree):
        """ This function allows to check if a SRS
            transformation to EPSG:4326 exists on
            the XML file.

        Args:
            xml_tree (ElementTree): tree to review

        Returns:
            bool: True if transformation is good

        """

        # Get step from XML file
        __steps = xml_tree.findall('step')

        # Check if any step exists
        if __steps is None:
            return False

        # Create variable for transformation
        __step_t = None

        # Iterate over steps
        for __step in __steps:

            # Get type if it exists
            __step_type = __step.find('type')

            # Check if type is transformation
            if __step_type.text == 'SRSTransformation':
                __step_t = __step
                break

        # Check if type was found
        if __step_t is None:
            return False

        # Create variable for SRS
        __step_s = None

        # Iterate over transformation's children
        for __step in __step_t:

            # Get target if it exists
            if __step.tag == 'target_srs':
                __step_s = __step
                break

        # Check if target was found
        if __step_s is None:
            return False

        # Create flags for result
        __step_a = False
        __step_r = False

        # Iterate over SRS's children
        for __step in __step_s:

            # Check SRS's authority
            if __step.tag == 'authority' and \
               __step.text == 'EPSG':
                __step_a = True

            # Check SRS's code
            if __step.tag == 'srid' and \
               __step.text == '4326':
                __step_r = True

        return __step_a and __step_r

    def get_steps(self, xml_tree):
        """ This function allows to get all the
            steps from the XML file.

        Args:
            xml_tree (ElementTree): tree to review

        Returns:
            list: found steps' name

        """

        # Get steps from XML file
        __steps = xml_tree.findall('step')

        # Check if any step exist
        if __steps is None:
            return None

        # Create structure for information
        __info = []

        # Iterate over steps
        for __step in __steps:

            # Get name if it exists
            __step_name = __step.find('name')

            # Check if name is valid
            if __step_name is None:
                return None
            elif __step_name.text == '':
                return None
            else:
                __info.append(__step_name.text)

        return __info

    def check_transform(self, path, checks=True):
        """ This function allows to check all
            the possible issues on the
            transformation XML file.

        Args:
            path (string): file's path
            checks (bool): checking flag

        Returns:
            dict: information about the outputs.

        """

        # Check if path is a correct file and exists
        if not os.path.exists(path) or not os.path.isfile(path):
            return settings.generate_error_file_not_found()

        # Detect flag of checking errors
        if not checks:
            return {
                'info_s': ['All the step executions were allowed.'],
                'info_f': ['All access to folders were allowed.'],
                'warn': [], 'error': []
            }

        # Check vulnerabilities
        __xml_tree = self.check_issues(path)
        if __xml_tree is None:
            return settings.generate_error_xml_vulnerabilities()

        # Check if steps are valid
        __no_steps, __valid_steps = self.check_steps(__xml_tree)
        if len(__no_steps):
            return settings.generate_error_xml_nodes_invalid(__no_steps, 'step')

        if not len(__valid_steps):
            return settings.generate_error_xml_node_not_found('steps')

        # Check if there is any folder and they are valid
        __no_steps, __no_folders, __valid_folders = \
            self.check_paths(path, __xml_tree, 'step')

        if len(__no_steps):
            return settings.generate_error_xml_nodes_invalid(__no_steps, 'step')

        if len(__no_folders):
            return settings.generate_error_xml_path_invalid(__no_folders)

        # Check if there is a mandatory target SRS
        if not self.check_srs(__xml_tree):
            return settings.generate_error_xml_node_srs_error()

        # Create return structure
        return {
            'error': [],
            'warn': [],
            'info_s': [
                'The ' + __step + ' execution was allowed.'
                for __step in __valid_steps
            ],
            'info_f': [
                'Access to ' + __folder + ' was allowed.'
                for __folder in __valid_folders
            ]
        }

    def check_job(self, path, checks=True):

        """ This function allows to check all
            the possible issues on the
            job XML file.

        Args:
            path (string): file's path
            checks (bool): checking flag

        Returns:
            dict: information about the outputs.

        """

        # Check if path is a correct file and exists
        if not os.path.exists(path) or not os.path.isfile(path):
            return settings.generate_error_file_not_found()

        # Check vulnerabilities
        __xml_tree = self.check_issues(path)
        if __xml_tree is None:
            return settings.generate_error_xml_vulnerabilities()

        # Detect flag of checking errors
        if not checks:
            return {
                'info_e': ['All the entries were allowed.'],
                'info_s': ['All the step executions were allowed.'],
                'info_f': ['All access to folders were allowed.'],
                'warn': [], 'error': []
            }

        # Check if there is any folder and they are valid
        __xml_tree = __xml_tree.find('entries')
        if __xml_tree is None:
            return settings.generate_error_xml_vulnerabilities()

        # Check if entries are valid
        __no_entries, __valid_entries = self.check_entries(__xml_tree)
        if len(__no_entries):
            return settings.generate_error_xml_nodes_invalid(__no_entries, 'entry')

        if not len(__valid_entries):
            return settings.generate_error_xml_node_not_found('entries')

        # Check if there is any folder and they are valid
        __no_entries, __no_folders, __valid_folders = \
            self.check_paths(path, __xml_tree, 'entry')

        if len(__no_entries):
            return settings.generate_error_xml_nodes_invalid(__no_entries, 'entry')

        if len(__no_folders):
            return settings.generate_error_xml_path_invalid(__no_folders)

        # Create return structure
        __return = {
            'info_e': [
                'The ' + __entry + ' entry was allowed.'
                for __entry in __valid_entries
            ],
            'info_s': set(), 'info_f': set(),
            'warn': [], 'error': []
        }

        # Check transformations from job file
        for __transform_path in __valid_folders:
            __transform_info = self.check_transform(__transform_path)

            # Check transformation errors
            if len(__transform_info['error']):
                __transform_info['error'] = \
                    [__transform_path] + __transform_info['error']
                return __transform_info

            # Save messages to structure
            __return['info_s'] = __return['info_s'].union(
                set(__transform_info['info_s'])
            )
            __return['info_f'] = __return['info_f'].union(
                set(__transform_info['info_f'])
            )

        __return['info_s'] = list(__return['info_s'])
        __return['info_f'] = list(__return['info_f'])

        return __return
