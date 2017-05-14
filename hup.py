#!/usr/bin/python3
#!python3
#encoding:utf-8
import sys
import os.path
import subprocess
import configparser
import argparse
import web.service.github.api.v3.Client
import database.src.Create
import cui.uploader.Main
import cui.account.Main

class Main:
    def __init__(self):
        pass

    def Run(self):
        parser = argparse.ArgumentParser(
            description='GitHub Repository Uploader.',
        )
        sub_parser = parser.add_subparsers()

        # accountサブコマンド
        parser_account = sub_parser.add_parser('account', help='see `account -h`')
        parser_account.add_argument('-u', '--username', '--user')
        parser_account.add_argument('-p', '--password', '--pass')
        parser_account.add_argument('-m', '--mailaddress', '--mail')
        parser_account.add_argument('-s', '--ssh-public-key-file-path', '--ssh')
        parser_account.add_argument('-t', '--two-factor-secret-key', '--two')
        parser_account.add_argument('-r', '--two-factor-recovery-code-file-path', '--recovery')
        parser_account.set_defaults(handler=self.__Account)

        # uploadサブコマンド
        parser_upload = sub_parser.add_parser('upload', help='see `upload -h`')
        parser_upload.add_argument('path_dir_pj')
        parser_upload.add_argument('-u', '--username')
        parser_upload.add_argument('-d', '--description')
        parser_upload.add_argument('-l', '--homepage', '--link', '--url')
        parser_upload.set_defaults(handler=self.__Upload)
        
        # コマンドライン引数をパースして対応するハンドラ関数を実行
        args = parser.parse_args()
        if hasattr(args, 'handler'):
            args.handler(args)
        else:
            # 未知のサブコマンドの場合はヘルプを表示
            parser.print_help()

        """
        args = parser_upload.parse_args()
        
        parser.add_argument('path_dir_pj')
        parser.add_argument('-u', '--username')
        parser.add_argument('-d', '--description')
        parser.add_argument('-l', '--homepage', '--link', '--url')
        args = parser.parse_args()
        print(args)
        print('path_dir_pj: {0}'.format(args.path_dir_pj))
        print('-u: {0}'.format(args.username))
        print('-d: {0}'.format(args.description))
        print('-l: {0}'.format(args.homepage))

        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.ini'))
        path_dir_db = os.path.abspath(config['Path']['DB'])
        print(path_dir_db)
        
        if None is args.username:
            args.username = config['GitHub']['User']
            print('default-username: {0}'.format(args.username))
        print(os.path.join(path_dir_db, 'GitHub.Accounts.sqlite3'))
        print(os.path.join(path_dir_db, 'GitHub.Repositories.{0}.sqlite3'.format(args.username)))
        
        data = database.src.Data.Data(args.path_dir_pj, path_dir_db, args.username, args.description, args.homepage)
        client = web.service.github.api.v3.Client.Client(data)

        creator = database.src.Create.InitializeMasterDbCreator(data, client)
        data = creator.Run()

        main = cui.uploader.Main.Main(data, client)
        main.Run()
        """

    def __Account(self, args):
        main = cui.account.Main.Main()
        main.Run(args)

    def __Upload(self, args):
        print('Uploadサブコマンド。')
        print(args)

        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.ini'))
        path_dir_db = os.path.abspath(config['Path']['DB'])
        print(path_dir_db)
        
        if None is args.username:
            args.username = config['GitHub']['User']
            print('default-username: {0}'.format(args.username))
        print(os.path.join(path_dir_db, 'GitHub.Accounts.sqlite3'))
        print(os.path.join(path_dir_db, 'GitHub.Repositories.{0}.sqlite3'.format(args.username)))
        
        data = database.src.Data.Data(args.path_dir_pj, path_dir_db, args.username, args.description, args.homepage)
        client = web.service.github.api.v3.Client.Client(data)

        creator = database.src.Create.InitializeMasterDbCreator(data, client)
        data = creator.Run()

        main = cui.uploader.Main.Main(data, client)
        main.Run()

if __name__ == '__main__':
    main = Main()
    main.Run()
