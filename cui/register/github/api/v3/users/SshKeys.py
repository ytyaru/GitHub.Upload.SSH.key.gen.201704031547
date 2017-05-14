#!python3
#encoding:utf-8
import requests
import datetime
import time
import json
import web.service.github.api.v3.Response
class SshKeys(object):
    def __init__(self):
        self.__response = web.service.github.api.v3.Response.Response()

    def Create(self, token, mailaddress, public_key):
        url = 'https://api.github.com/user/keys'
        headers=self.__GetHeaders(token)
        data=json.dumps({'title': mailaddress, 'key': public_key})
        print(url)
        print(data)
        r = requests.post(url, headers=headers, data=data)
        return self.__response.Get(r)
        
    def __GetHeaders(self, token, otp=None):
        headers = {
            'Time-Zone': 'Asia/Tokyo',
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': 'token ' + token
        }
        if None is not otp:
            headers.update({'X-GitHub-OTP': otp})
        print(headers)
        return headers
