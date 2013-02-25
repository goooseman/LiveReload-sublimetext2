#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import threading
import subprocess
import sys
import sublime
import sublime_plugin
import shlex

# fix for import order

sys.path.append(os.path.join(sublime.packages_path(), 'LiveReload'))
LiveReload = __import__('LiveReload')
sys.path.remove(os.path.join(sublime.packages_path(), 'LiveReload'))


class CompassThread(threading.Thread):

    def getLocalOverride(self):
        """
        You can override defaults in sublime-project file
        
        Discussion: https://github.com/dz0ny/LiveReload-sublimetext2/issues/43
        
        Example: 

            "settings": {
              "lrcompass": {
                "dirname": "/path/to/directory/which/contains/config.rb",
                "command": "compass compile -e production --force"
              }
            }
        """
        view_settings = sublime.active_window().active_view().settings()
        view_settings = view_settings.get('lrcompass')
        if view_settings:
            return view_settings
        else:
            return {}

    def __init__(self, dirname, on_compile):

        self.dirname = self.getLocalOverride.get('dirname') \
            or dirname.replace('\\', '/')
        self.command = self.getLocalOverride.get('command') or 'compass compile'
        self.stdout = None
        self.stderr = None
        self.on_compile = on_compile
        threading.Thread.__init__(self)

    def run(self):
        cmd = shlex.split(self.command)
        cmd.append(self.dirname)
        p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        if p.stdout.read():
            self.on_compile()


class CompassPreprocessor(LiveReload.Plugin,
    sublime_plugin.EventListener):

    title = 'Compass Preprocessor'
    description = 'Compile and refresh page, when file is compiled'
    file_types = '.scss,.sass'
    this_session_only = True
    file_name = ''

    def on_post_save(self, view):
        self.original_filename = os.path.basename(view.file_name())
        if self.should_run(self.original_filename):
            self.file_name_to_refresh = \
                self.original_filename.replace('.scss', '.css'
                    ).replace('.sass', '.css')
            dirname = os.path.dirname(view.file_name())
            CompassThread(dirname, self.on_compile).start()

    def on_compile(self):
        settings = {
            'path': self.file_name_to_refresh,
            'apply_js_live': False,
            'apply_css_live': True,
            'apply_images_live': True,
            }
        self.sendCommand('refresh', settings, self.original_filename)
