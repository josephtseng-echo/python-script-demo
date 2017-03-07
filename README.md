python script dev 目录规范
===
```
├── bin               //打包成二进制文件运行<br/>
├── data<br/>
│   ├── logging.conf  //日志配置文件<br/>
│   ├── product.conf  //生产环境配置文件<br/>
│   └── test.conf     //测试环境配置文件<br/>
├── logs<br/>
│   └── app.log       //应用log<br/>
└── src<br/>
    ├── base.py       //基类库<br/>
    ├── main.py       //主类<br/>
    └── todo.py       //TODO<br/>

使用 cxfreeze src/main.py --target-dir bin 打包<br/>

方便以后自己开发py script都可以按这目录结构<br/>

使用：<br/>
cd src; python2.7 main.py test or python2.7 main.py product<br/>
或<br/>
通过打包后<br/>
cd bin; python2.7 run test or run product
```
