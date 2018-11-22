#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import urllib2
import time
import mimetypes
import numpy as np
import os
import smtplib
from email.mime.base import MIMEBase
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email import encoders


# encoding=utf8
import sys

reload(sys)
sys.setdefaultencoding('utf8')


# 蒲公英用
#蒲公英应用上传地址
url = 'https://www.pgyer.com/apiv2/app/upload'
#蒲公英提供的 用户Key
uKey = 'AAAAAAAAAAAAAAAAAAAAAA'
#蒲公英提供的 API Key
_api_key = 'BBBBBBBBBBBBBBBBBBBBB'
#(选填)应用安装方式，值为(1,2,3)。1：公开，2：密码安装，3：邀请安装。默认为1公开
buildInstallType = '2'
#(选填) 设置App安装密码，如果不想设置密码，请传空字符串，或不传。
buildPassword = '123456'


# 运行时环境变量字典
environsDict = os.environ
#print environsDict

#此次 jenkins 构建版本号
jenkins_build_number = environsDict['BUILD_TAG']
print jenkins_build_number

#获取附件路径
path = './build/ipa-build'#指定文件所在路径
filetype ='.ipa'#指定文件类型


def get_filename(path,filetype):
    name =[]
    final_name = []
    for root,dirs,files in os.walk(path):
        for i in files:
            if filetype in i:
                name.append(i.replace(filetype,''))#生成不带‘.ipa’后缀的文件名组成的列表
    final_name = [item +'.ipa' for item in name]#生成‘.ipa’后缀的文件名组成的列表
    return final_name#输出由有‘.ipa’后缀的文件名组成的列表

ipa_file_path = get_filename(path,filetype)[0]
print ipa_file_path


#请求字典编码
def _encode_multipart(params_dict):
    boundary = '----------%s' % hex(int(time.time() * 1000))
    data = []
    for k, v in params_dict.items():
        data.append('--%s' % boundary)
        if hasattr(v, 'read'):
            filename = getattr(v, 'name', '')
            content = v.read()
            decoded_content = content.decode('ISO-8859-1')
            data.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (k,ipa_file_path))
            data.append('Content-Type: application/octet-stream\r\n')
            data.append(decoded_content)
        else:
            data.append('Content-Disposition: form-data; name="%s"\r\n' % k)
            data.append(v if isinstance(v, str) else v.decode('utf-8'))
    data.append('--%s--\r\n' % boundary)
    return '\r\n'.join(data), boundary


#处理 蒲公英 上传结果
def handle_resule(result):
    json_result = json.loads(result)
    print '*******上传蒲公英****'
    print json_result
    if json_result['code'] is 0:
        print '*******文件上传成功****'
        #        print  json_result
        send_Email(json_result)

#发送邮件
def send_Email(json_result):
    print '*******开始发送邮件****'
    buildName = os.getenv('appName')
    buildVersionCode = os.getenv('versionCode')
    buildEid = os.getenv('eId')
    buildRemark = os.getenv('remark')
    buildQRCodeURL = json_result['data']['buildQRCodeURL']
    
    choice = os.getenv('regist_show')
    print choice
    if choice == 'true':
        buildRegistShow = "手机自注册登入"
        print buildRegistShow
    else:
        buildRegistShow = "非手机自注册登入"
        print buildRegistShow

    print "if 判断结束"
    print buildRegistShow

    #邮件接受者
    mail_receiver = ['receiver_one@mail.com','receiver_two@mail.com']


    #根据不同邮箱配置 host，user，和pwd
    mail_host = 'your mail host'
    mail_port = 25
    mail_user = 'your email'
    mail_pwd = 'email password'
    mail_to = ','.join(mail_receiver)
    
    msg = MIMEMultipart()
    
    environsString = '<h3>本次打包相关信息</h3><p>'
    environsString += '<p>应用名称：'+ str(buildName) +'</p>'
    environsString += '<p>软件版本：V2.x</p>'
    environsString += '<p>企业ID：'+ str(buildEid) +'</p>'
    environsString += '<p>内部版本号：'+ str(buildVersionCode) +'</p>'
    environsString += '<p>登录模式：'+ str(buildRegistShow) +'</p>'
    environsString += '<p>此安装包描述文件过期时间为****年**月**日。</p>'
    environsString += '<p>附件是iOS安装包，请查收。</p>'
    
    if buildRemark:
        print "buildRemark not empty"
        environsString += '<p>'+ str(buildRemark) +'</p>'
    else:
        print "buildRemark empty"
        print buildRemark

    environsString += '<img src="'+ str(buildQRCodeURL) +'"  alt="二维码" />'
    environsString += '<p>扫码直接安装，安装密码:'+ str(buildPassword) +'</p>'

    message = environsString
    body = MIMEText(message, _subtype='html', _charset='utf-8')
    
    
    #    添加附件
    part = MIMEBase('application', 'octet-stream')                          # 'octet-stream': binary data   创建附件对象
    source_path = './build/ipa-build/' + ipa_file_path
    part.set_payload(open(source_path, 'rb').read())                        # 将附件源文件加载到附件对象
    encoders.encode_base64(part)

    part_name = ipa_file_path
    part_name = part_name.decode('utf-8').encode(sys.getfilesystemencoding())
    print part_name

    part.add_header('Content-Disposition', 'attachment', filename=part_name)# 给附件添加头文件
    
    msg.attach(body)
    msg.attach(part)    # 将附件附加到根容器
    msg['To'] = mail_to
    msg['from'] = mail_user
    msg['subject'] = '【打包文件】' + ' ' + buildEid +' '+ buildRegistShow +' '+ buildName + ' iOS安装包 '
    
    try:
        s = smtplib.SMTP()
        # 设置为调试模式，就是在会话过程中会有输出信息
#        s.set_debuglevel(1)
        s.connect(mail_host)
        s.login(mail_user, mail_pwd)
        
        s.sendmail(mail_user, mail_receiver, msg.as_string())
        s.close()
        
        print '*******邮件发送成功****'
    except Exception, e:
        print e

#############################################################


#send_Email(ipa_file_path)
source_path = './build/ipa-build/' + ipa_file_path
#请求参数字典
params = {
    '_api_key': _api_key,
    'file': open(source_path, 'rb'),
    'buildInstallType': buildInstallType,
    'buildPassword': buildPassword

}

coded_params, boundary = _encode_multipart(params)
req = urllib2.Request(url, coded_params.encode('ISO-8859-1'))
req.add_header('Content-Type', 'multipart/form-data; boundary=%s' % boundary)
try:
    print '*******开始文件上传****'
    resp = urllib2.urlopen(req)
    body = resp.read().decode('utf-8')
    handle_resule(body)

except urllib2.HTTPError as e:
    print(e.fp.read())

