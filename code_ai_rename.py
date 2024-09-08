"""
Renames code variables in a given Source tree 
"""
import argparse
import os
import subprocess
import logging
import sys
import tqdm
from ctags import CTags, TagEntry
import ollama


class AiFileAgent:
    """A runner to analyze a file with code"""
    def __init__(self, filename) -> None:
        self.filename = filename
        self.symbol_dict = {}

    def get_symbols(self):
        """Asks ollama LLM to analyze code in file, and provide better variable names"""
        with open(self.filename, 'r', encoding='utf-8') as file:
            code = file.read()
            tagFile = CTags('tags')
            response = ollama.chat(model='llama2',
                               messages=[{
                                   'role': 'user',
                                   'content': 'Your task is to read the given code, then know the'
                                   'purpose of each variable as one sentance description. Then use '
                                   'simple language so the description is understandable by a '
                                   'junior programmer. Then propose a single good name for each '
                                   'variable in camel case. The expected output would be in csv '
                                   'with 2 columns, found variable name and proposed new variable '
                                   'name. The code is :\n' + code, }])
            logging.debug(response['message']['content'])


class AiRename:
    """ 
    AiRename class walks a directory for a file pattern, gets all variables within the found files,
    and finally renames them using information from an AI chat model. 
    """
    src_files = []  # Holds all source file agents. When agents are run,
                    # file symbols will be renamed
    arg = argparse.Namespace()
    @staticmethod
    def run(arg):
        """ App entry point """
        logging.info("Welcome to: Code AI Renamer!")
        logging.debug("Starting with args:")
        logging.debug(arg)
        AiRename.arg = arg
        for root, _, files in os.walk(arg.directory):
            for file in files:
                if file.endswith(AiRename.get_extensions()):
                    current_file = os.path.join(root, file)
                    logging.debug(current_file)
                    AiRename.src_files.append(AiFileAgent(current_file))
        logging.info("Found %s files matching: %s",
                     str(len(AiRename.src_files)),
                     str(AiRename.get_extensions()))
        subprocess.run(["ctags", "--fields=afmikKlnsStz",
                        "--languages="+AiRename.get_ctags_extensions(),
                        "-R", arg.directory],
                       check=True)
        for a in tqdm.tqdm(AiRename.src_files, file=sys.stdout):
            a.get_symbols()

    @staticmethod
    def get_extensions():
        """ Concatenates all enabled file extensions for the file walker
        Returns:
          typle: all configured extensions
        """
        if not AiRename.arg:
            raise KeyError("Sorry, cannot access args before class entry point: run!")
        arg = AiRename.arg
        ext = []
        if arg.c:
            ext.append(".c")
            ext.append(".h")
        if arg.cpp:
            ext.append(".cpp")
            ext.append(".hpp")
        if arg.java:
            ext.append(".java")
        if arg.js:
            ext.append(".js")
        if arg.ts:
            ext.append(".ts")
        if arg.python:
            ext.append(".py")
        if hasattr(arg.others, '__iter__'):
            for o in arg.others:
                ext.append("."+o)
        return tuple(ext)

    @staticmethod
    def get_ctags_extensions():
        """ Concatenates all enabled file extensions for CTAGS
        Returns:
          csv: all configured langauges
        """
        if not AiRename.arg:
            raise KeyError("Sorry, cannot access args before class entry point: run!")
        arg = AiRename.arg
        ext = []
        if arg.c:
            ext.append("C")
        if arg.cpp:
            ext.append("C++")
        if arg.java:
            ext.append("Java")
        if arg.python:
            ext.append("Python")
        #TODO: Complete other language mapping. Check: ctags --list-languages
        return ','.join(ext)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Rename code symbols using AI.')
    parser.add_argument("-d", "--directory", required=True, default="src",
                        help="Root directory for source code")
    parser.add_argument("--c",  action='store_true',
                        help="Include all *.c and *.h sources")
    parser.add_argument("--cpp",  action='store_true',
                        help="Include all *.cpp and *.hpp sources")
    parser.add_argument("--java",  action='store_true',
                        help="Include all *.java sources")
    parser.add_argument("--js",  action='store_true',
                        help="Include all *.js sources")
    parser.add_argument("--ts",  action='store_true',
                        help="Include all *.ts sources")
    parser.add_argument("--python",  action='store_true',
                        help="Include all *.py sources")
    parser.add_argument("--others",  nargs='+',
                        help="Add other arbitrary extensions. Example: --others tcl sh.")
    parser.add_argument("--in-place",  action='store_true',
                        help="Rename code in place. Otherwise a <directory>_renamed is created.")
    logging.basicConfig(stream=sys.stderr, format= '  %(levelname)-8s%(module)-10s: %(message)s',
                        level=logging.DEBUG) # debug, info, warning, error and critical.
    AiRename().run(parser.parse_args())
