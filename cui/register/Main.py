#!/usr/bin/python3
#!python3
#encoding:utf-8
import os.path
import subprocess
import shlex
import dataset
import database.src.Database
import database.src.account.Main
import cui.register.github.api.v3.authorizations.Authorizations
import cui.register.github.api.v3.users.SshKeys
import web.sqlite.Json2Sqlite
class Main:
    def __init__(self, path_dir_db):
        self.path_dir_db = path_dir_db
        self.j2s = web.sqlite.Json2Sqlite.Json2Sqlite()
        self.__db = None
    def Insert(self, args):
        print('Account.Insert')
        print(args)
        print('-u: {0}'.format(args.username))
        print('-p: {0}'.format(args.password))
        print('-m: {0}'.format(args.mailaddress))
        print('-s: {0}'.format(args.ssh_public_key_file_path))
        print('-t: {0}'.format(args.two_factor_secret_key))
        print('-r: {0}'.format(args.two_factor_recovery_code_file_path))
        print('--auto: {0}'.format(args.auto))

        self.__db = database.src.Database.Database()
        self.__db.Initialize()
        
        account = self.__db.account['Accounts'].find_one(Username=args.username)
        print(account)
        if None is account:
            # 1. APIでメールアドレスを習得する。https://developer.github.com/v3/users/emails/
            # 2. Tokenの新規作成
            auth = cui.register.github.api.v3.authorizations.Authorizations.Authorizations(args.username, args.password)
            token_repo = auth.Create(args.username, args.password, scopes=['repo'])
            token_delete_repo = auth.Create(args.username, args.password, scopes=['delete_repo'])
            token_user = auth.Create(args.username, args.password, scopes=['user'])
            token_public_key = auth.Create(args.username, args.password, scopes=['admin:public_key'])
            # 3-1. SSH鍵の新規作成
            ssh_key_gen_params = self.__SshKeyGen(args.username, args.mailaddress)
            host = self.__SshConfig(args.username, ssh_key_gen_params['path_file_key_private'])
#            self.__db.account['SshConfigures'].insert(self.__CreateRecordSshConfigures(account['Id'], host, ssh_key_gen_params))
            # 3-2. SSH鍵をGitHubに登録してDBに挿入する
            api_ssh = cui.register.github.api.v3.users.SshKeys.SshKeys()
            j_ssh = api_ssh.Create(token_public_key['token'], args.mailaddress, ssh_key_gen_params['public_key'])
#            self.__db.account['SshKeys'].insert(self.__CreateRecordSshKeys(account['Id'], j_ssh))
            # 4. 全部成功したらDBにアカウントを登録する
#            args.mailaddress = APIで取得する
            self.__db.account['Accounts'].insert(self.__CreateRecordAccount(args))
            account = self.__db.account['Accounts'].find_one(Username=args.username)
            if None is not args.two_factor_secret_key:
                self.__db.account['AccessTokens'].insert(self.__CreateRecordTwoFactor(account['Id'], args))
            self.__db.account['AccessTokens'].insert(self.__CreateRecordToken(account['Id'], token_repo))
            self.__db.account['AccessTokens'].insert(self.__CreateRecordToken(account['Id'], token_delete_repo))
            self.__db.account['AccessTokens'].insert(self.__CreateRecordToken(account['Id'], token_user))
            self.__db.account['AccessTokens'].insert(self.__CreateRecordToken(account['Id'], token_public_key))
            self.__db.account['SshConfigures'].insert(self.__CreateRecordSshConfigures(account['Id'], host, ssh_key_gen_params))
            self.__db.account['SshKeys'].insert(self.__CreateRecordSshKeys(account['Id'], ssh_key_gen_params['private_key'], ssh_key_gen_params['public_key'], j_ssh))

        # 作成したアカウントのリポジトリDB作成や、作成にTokenが必要なライセンスDBの作成
        self.__db.Initialize()
        return self.__db

    def __CreateRecordAccount(self, args):
        return dict(
            Username=args.username,
            MailAddress=args.mailaddress,
            Password=args.password,
            CreateAt="1970-01-01T00:00:00Z"
        )
        # 作成日時はAPIのuser情報取得によって得られる。
        
    def __CreateRecordToken(self, account_id, j):
        return dict(
            AccountId=account_id,
            IdOnGitHub=j['id'],
            Note=j['note'],
            AccessToken=j['token'],
            Scopes=self.j2s.ArrayToString(j['scopes'])
        )

    def __CreateRecordTwoFactor(self, account_id, args):
        return dict(
            AccountId=account_id,
            Secret=args.args.two_factor_secret_key
        )
        
    def __SshKeyGen(self, username, mailaddress):
        # SSH鍵の生成
        path_dir_ssh = os.path.join(os.path.expanduser('~'), '.ssh/')
#        path_dir_ssh = "/tmp/.ssh/" # テスト用
        path_dir_ssh_keys = os.path.join(path_dir_ssh, 'github/')
        if not(os.path.isdir(path_dir_ssh_keys)):
            os.makedirs(path_dir_ssh_keys)
        protocol_type = "rsa" # ["rsa", "dsa", "ecdsa", "ed25519"]
        bits = 4096 # 2048以上推奨
        passphrase = '' # パスフレーズはあったほうが安全らしい。忘れるだろうから今回はパスフレーズなし。
        path_file_key_private = os.path.join(path_dir_ssh_keys, 'rsa_{0}_{1}'.format(bits, username))
        print(path_dir_ssh)
        print(path_dir_ssh_keys)
        print(path_file_key_private)
        command = 'ssh-keygen -t {p_type} -b {bits} -P "{passphrase}" -C "{mail}" -f "{path}"'.format(p_type=protocol_type, bits=bits, passphrase=passphrase, mail=mailaddress, path=path_file_key_private)
        print(command)
        subprocess.call(shlex.split(command))
        
        private_key = None
        with open(path_file_key_private, 'r') as f:
            private_key = f.read()
        public_key = None
        with open(path_file_key_private + '.pub', 'r') as f:
            public_key = f.read()
        
        ssh_key_gen_params = {
            'type': protocol_type,
            'bits': bits,
            'passphrase': passphrase,
            'path_file_key_private': path_file_key_private,
            'path_file_key_public': path_file_key_private + '.pub',
            'private_key': private_key,
            'public_key': public_key,
        }
        return ssh_key_gen_params
#        return path_file_key_private

    def __SshConfig(self, username, IdentityFile, Port=22):
        host = 'github.com.{username}'.format(username=username)
        append = '''\
Host {Host}
  User git
  Port {Port}
  HostName github.com
  IdentityFile {IdentityFile}
  TCPKeepAlive yes
  IdentitiesOnly yes
'''
        append = append.format(Host=host, Port=Port, IdentityFile=IdentityFile)
        print(append)
        path_dir_ssh = os.path.join(os.path.expanduser('~'), '.ssh/')
#        path_dir_ssh = "/tmp/.ssh/" # テスト用
        path_file_config = os.path.join(path_dir_ssh, 'config')
        if not(os.path.isfile(path_file_config)):
            with open(path_file_config, 'w') as f:
                pass        
        # configファイルの末尾に追記する
        with open(path_file_config, 'a') as f:
            f.write(append)
        
        return host

    def __CreateRecordSshConfigures(self, account_id, host, ssh_key_gen_params):
        return dict(
            AccountId=account_id,
            HostName=host,
            PrivateKeyFilePath=ssh_key_gen_params['path_file_key_private'],
            PublicKeyFilePath=ssh_key_gen_params['path_file_key_public'],
            Type=ssh_key_gen_params['type'],
            Bits=ssh_key_gen_params['bits'],
            Passphrase=ssh_key_gen_params['passphrase'],
        )

    def __CreateRecordSshKeys(self, account_id, private_key, public_key, j):
        return dict(
            AccountId=account_id,
            Title=j['title'],
            Key=j['key'],
            PrivateKey=private_key,
            PublicKey=public_key,
            Verified=self.j2s.BoolToInt(j['verified']),
            ReadOnly=self.j2s.BoolToInt(j['read_only']),
            CreatedAt=j['created_at'],
        )

    def Update(self, args):
        print('Account.Update')
        print(args)
        print('-u: {0}'.format(args.username))
        print('-p: {0}'.format(args.password))
        print('-m: {0}'.format(args.mailaddress))
        print('-s: {0}'.format(args.ssh_public_key_file_path))
        print('-t: {0}'.format(args.two_factor_secret_key))
        print('-r: {0}'.format(args.two_factor_recovery_code_file_path))
        print('--auto: {0}'.format(args.auto))

    def Delete(self, args):
        print('Account.Delete')
        print(args)
        print('-u: {0}'.format(args.username))
        print('--auto: {0}'.format(args.auto))

    def Tsv(self, args):
        print('Account.Tsv')
        print(args)
        print('path_file_tsv: {0}'.format(args.path_file_tsv))
        print('--method: {0}'.format(args.method))

