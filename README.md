# pyzdns
zdns调度工具
> 自行安装zdns后指定路径
> 以centos为例安装zdns
>
```shell script
wget https://storage.googleapis.com/golang/go1.10.4.linux-amd64.tar.gz
tar -C /usr/local -xzf go1.10.4.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin
export GOPATH=/usr/local/go/bin/
go get github.com/zmap/zdns
cd $GOPATH/bin/src/github.com/zmap/zdns/zdns
go build
```

> 字典使用layer子域名挖掘机工具的字典
> 
by:李大侠