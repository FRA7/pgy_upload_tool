# coding=utf-8

"""
    * User:  fraj
    * Email: fraj@foxmail.com
    * Date:  18/2/1
    * Time:  10:00
    
    """


import time
import urllib2
import time
import json
import mimetypes
import os
import smtplib
from email.mime.base import MIMEBase
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email import encoders

import json

# encoding=utf8
import sys

reload(sys)
sys.setdefaultencoding('utf8')

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

#此次 jenkins 构建环境  ZHDJ_COMMON 为商用环境   ZHDJ_TEST 为商测环境
sel_product_flavors = os.getenv('PRODUCT_FLAVORS')
print sel_product_flavors

#此次 jenkins 构建变更记录
changelog = os.getenv('SCM_CHANGELOG')
print '*******changelog****'
print changelog

#获取 ipa 文件路径
def get_ipa_file_path():
    #工作目录下面的 ipa 文件
    ipa_file_workspace_path = './your_app.ipa'
    
    if os.path.exists(ipa_file_workspace_path):
        return ipa_file_workspace_path

# while get_ipa_file_path() is None:
#     time.sleep(5)

#ipa 文件路径
ipa_file_path = get_ipa_file_path()
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
            data.append('Content-Disposition: form-data; name="%s"; filename="zqreader.ipa"' % k)
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
    buildName = json_result['data']['buildName']
    buildKey = json_result['data']['buildKey']
    buildVersion = json_result['data']['buildVersion']
    buildBuildVersion = json_result['data']['buildBuildVersion']
    buildShortcutUrl = json_result['data']['buildShortcutUrl']
    buildQRCodeURL = json_result['data']['buildQRCodeURL']
    buildUpdated = json_result['data']['buildUpdated']
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
    environsString += '<p>应用名称:'+ str(buildName) +'</p>'
    environsString += '<p>版本号:'+ str(buildVersion) +'</p>'
    environsString += '<p>更新时间:'+ str(buildUpdated) +'</p>'
    environsString += '<p>安装密码:'+ str(buildPassword) +'</p>'
    if changelog:
        print "changelog not empty"
        environsString += '<p>变更记录:</p>'
        environsString += '<p>'+ str(changelog) +'</p>'
    else:
        print "changelog empty"


    #    environsString += '<p>你可从蒲公英网站在线安装 : ' + 'http://www.pgyer.com/' + str(buildShortcutUrl) + '<p>'
    environsString += '<img src="'+ str(buildQRCodeURL) +'"  alt="二维码" />'
    environsString += '<p>扫码直接安装</p>'
    message = environsString
    body = MIMEText(message, _subtype='html', _charset='utf-8')
    
    
    #    添加附件
    part = MIMEBase('application', 'octet-stream')                          # 'octet-stream': binary data   创建附件对象
    source_path = get_ipa_file_path()
    part.set_payload(open(source_path, 'rb').read())                        # 将附件源文件加载到附件对象
    encoders.encode_base64(part)
    nowTime = time.strftime("%Y-%m-%d", time.localtime())
    part_name = 'your_app-' + nowTime + '_'+ sel_product_flavors +'.ipa'
    part_name = part_name.decode('utf-8').encode(sys.getfilesystemencoding())
    print part_name
    part.add_header('Content-Disposition', 'attachment; filename="' + part_name +'"')     # 给附件添加头文件
    
    msg.attach(body)
    msg.attach(part)    # 将附件附加到根容器
    msg['To'] = mail_to
    msg['from'] = mail_user
    msg['subject'] = 'iOS打包文件: ' + sel_product_flavors + ' ' + buildName +' '+ buildVersion
    
    try:
        s = smtplib.SMTP()
        # 设置为调试模式，就是在会话过程中会有输出信息
        s.set_debuglevel(1)
        s.connect(mail_host)
        s.login(mail_user, mail_pwd)
        
        s.sendmail(mail_user, mail_receiver, msg.as_string())
        s.close()
        
        print '*******邮件发送成功****'
    except Exception, e:
        print e

#############################################################
#请求参数字典
params = {
    '_api_key': _api_key,
    'file': open(ipa_file_path, 'rb'),
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

