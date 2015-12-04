pbMerge
=========
pbMerge.py，是一个python脚本，它能够对两个Xcode中的工程文件project.pbxproj进行预合并，对错乱的object进行排序，把相同的放前面，接着放uuid不同或只是filename不同的object，最后放两边完全不同的object。如下面预合并前的两个文件：

![处理前的工程文件对比](http://upload-images.jianshu.io/upload_images/972306-5c894b3e89dc6b2c.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

经过脚本预合并后：

![预合并后工程文件的比较](http://upload-images.jianshu.io/upload_images/972306-55230a05fe4cba7c.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/1240)

使用方法
=============

```
$ python pbMerge.py project1.pbxproj project1.pbxproj
```

运行后会产生两个新的工程文件 project1.pbxproj.merge 和 project1.pbxproj.merge，再用第三方比较工具进行合并即可。


