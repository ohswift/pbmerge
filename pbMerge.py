#coding:utf-8

"""
pbMerge.py
Copyright 2015 Vincent Yu <mightyme@qq.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import os
import re
import sys

gBuidFileSectionPattern = re.compile(r'''(?i)(.*/\* Begin PBXBuildFile section \*/\s+?)(.*?)(/\* End PBXBuildFile section \*/.*)''', re.S)
gFileReferenceSectionPattern = re.compile(r'''(?i)(.*/\* Begin PBXFileReference section \*/\s+?)(.*?)(/\* End PBXFileReference section \*/.*)''', re.S)
gSourceBuildPhaseSectionPattern = re.compile(r'''(?i)(.*/\* Begin PBXSourcesBuildPhase section \*/\s+?)(.*?)(/\* End PBXSourcesBuildPhase section \*/.*)''', re.S)

gBuidFilePattern = re.compile(r'''(?i)(^\s+(\w+) /\* (\S*)\s.*?$)''', re.S|re.M)
gFileReferencePattern = gBuidFilePattern
gSourceBuildPhaseSourcePattern = re.compile(r'''(^\s+(\w+?) /\* Sources \*/.*?$.*?^\s+files.*?$\n)(.*?)(^\s+\);.*?};\n)''', re.S|re.M)

gSourceBuildPhaseFilePattern = gBuidFilePattern

# 加入辅助线区分
gConfigAssistLine = True
gLineFormat = 15*"=="

def compareFile(file1, file2):
    if file1[2]==file2[2]:
        if file1[1]==file2[1]:
            return 0
        return 1
    elif file1[1]==file2[1]:
        return 2
    return 3
    
def resortFiles(files1, files2):
    sameFiles=[]    # 左右都有的文件，而且uuid相同
    moveFiles=[]    # 左右都有的文件，但uuid不同，元素为tuple
    renameFiles=[]  # 左右一样的uuid，但是文件名不同, 元素为tuple
    leftFiles=[]    # 左边才有的文件
    rightFiles=[]   # 右边才有的文件
    i,res=0,2
    
    while i<len(files1):
        left=files1[i]
        j,res,right=0,2,None
        while j<len(files2):
            right=files2[j]
            res=compareFile(left, right)
            if (res!=3):
                del(files2[j])
                break
            j=j+1
        if res==0:
            sameFiles.append(left)
        elif res==1:
            moveFiles.append((left,right))
        elif res==2:
            renameFiles.append((left,right))
        elif res==3:
            leftFiles.append(left)
        
        del(files1[i])
    rightFiles += files2
    
    rfiles1,rfiles2=[],[]
    # 加入标识字段
    
    for f in sameFiles:
        rfiles1.append(f)
        rfiles2.append(f)
    if gConfigAssistLine and len(moveFiles):
        rfiles1.append(("/*"+gLineFormat+"= same filename,different uuid(files may be moved) ="+gLineFormat+"*/",))
        rfiles2.append((gLineFormat+"= same filename,different uuid(files may be moved) ="+gLineFormat+"*/",))
    for f in moveFiles:
        rfiles1.append(f[0])
        rfiles2.append(f[1])
    if gConfigAssistLine and len(renameFiles):
        rfiles1.append(("/*"+gLineFormat+"= same uuid,different filename(files may be renamed) ="+gLineFormat+"*/",))
        rfiles2.append(("/*"+gLineFormat+"= same uuid,different filename(files may be renamed) ="+gLineFormat+"*/",))
    for f in renameFiles:
        rfiles1.append(f[0])
        rfiles2.append(f[1])
    if gConfigAssistLine and len(leftFiles):
        rfiles1.append(("/*"+gLineFormat+"= files only exist at left ="+gLineFormat+"*/",)) 
    rfiles1 += leftFiles
    if gConfigAssistLine and len(rightFiles):
        rfiles2.append(("/*"+gLineFormat+"= files only exist at right ="+gLineFormat+"*/",)) 
    rfiles2 += rightFiles
    
    return (rfiles1, rfiles2)

def getBuildFiles(content):
    sections = re.findall(gBuidFileSectionPattern, content)
    if len(sections)==0:
        return (None, None, None)
    section = sections[0]
    # 前面部分和后面部分需要写回，中间的buildFile修改顺序
    prefix = section[0]
    subfix = section[2]
    middle = section[1]
    
    files = re.findall(gBuidFilePattern, middle)

    return (prefix, files, subfix)

def buildFilesToStr(files):
    rstr = ""
    for f in files:
        rstr += "%s\n" % f[0]
    return rstr

# 1. 对PBXBuildFile数据进行merge
def doMergeBuildFile(sContent,dContent):
    prefix1,files1,subfix1 = getBuildFiles(sContent)
    prefix2,files2,subfix2 = getBuildFiles(dContent)
    rFiles1,rFiles2 = resortFiles(files1, files2)
    sContent = prefix1+buildFilesToStr(rFiles1)+subfix1
    dContent = prefix2+buildFilesToStr(rFiles2)+subfix2
    
#     print "sContent:\n%s\n\n\n" % sContent
#     print "dContent:\n%s\n" % dContent
    return (sContent, dContent)

def getFileReferences(content):
    sections = re.findall(gFileReferenceSectionPattern, content)
    if len(sections)==0:
        return (None, None, None)
    section = sections[0]
    # 前面部分和后面部分需要写回，中间的buildFile修改顺序
    prefix = section[0]
    subfix = section[2]
    middle = section[1]
    
    files = re.findall(gFileReferencePattern, middle)

    return (prefix, files, subfix)

# 2. 对PBXFileReference数据进行merge
def doMergeFileReference(sContent,dContent):
    prefix1,files1,subfix1 = getFileReferences(sContent)
    prefix2,files2,subfix2 = getFileReferences(dContent)
    
    rFiles1,rFiles2 = resortFiles(files1, files2)
    sContent = prefix1+buildFilesToStr(rFiles1)+subfix1
    dContent = prefix2+buildFilesToStr(rFiles2)+subfix2

#     print "sContent:\n%s\n\n\n" % sContent
#     print "dContent:\n%s\n" % dContent    
    return (sContent, dContent)

def getSourceBuildPhaseSource(content):
    sections = re.findall(gSourceBuildPhaseSectionPattern, content)
    if len(sections)==0:
        return (None, None, None)
    section = sections[0]
    # 前面部分和后面部分需要写回，中间的buildFile修改顺序
    prefix = section[0]
    subfix = section[2]
    middle = section[1]
    
    sources = re.findall(gSourceBuildPhaseSourcePattern, middle)

    return (prefix, sources, subfix)
    pass
    
def compareSource(source1, source2):
    if source1[1]==source2[1]:
        return 0
    return 1
    
def resortSourceFileInSource(source1, source2):
    rsource1,rsource2=list(source1),list(source2)
    
    files1=re.findall(gSourceBuildPhaseFilePattern, source1[2])
    files2=re.findall(gSourceBuildPhaseFilePattern, source2[2])
    
    if len(files1)==0 or len(files2)==0:
        return (rsource1, rsource2)
    rfiles1,rfiles2 = resortFiles(files1, files2)
    # 修改tuple
    rsource1[2] = rfiles1
    rsource2[2] = rfiles2
    
    return (tuple(rsource1), tuple(rsource2))

def resortSources(sources1, sources2):
    sames,lefts,rights=[],[],[]
    i,j,left,right=0,0,None,None
    while i<len(sources1):
        left=sources1[i]
        j,res=0,0
        while j<len(sources2):
            right = sources2[j]
            res = compareSource(left, right) 
            if res==0:
                del(sources2[j])
                break
            j = j+1
        if res==0:
            sames.append(resortSourceFileInSource(left,right))
        else:
            lefts.append(left)
        del(sources1[i])
    rights += sources2
    rsources1,rsources2=[],[]
    for s in sames:
        rsources1.append(s[0])
        rsources2.append(s[1])
    rsources1 += lefts;
    rsources2 += rights;
    return (rsources1, rsources2)

def sourcesToStr(sources):
    rstr = ""
    for s in sources:
        rstr += "%s" % s[0]
        files = s[2]
        if type(files)==str:
            rstr += "%s" % files
        else:
            rstr += "%s" % buildFilesToStr(files)
        rstr += "%s" % s[3]
    return rstr

# 3. 对PBXSourcesBuildPhase数据进行merge
def doMergeSourceBuildPhase(sContent,dContent):
    prefix1,sources1,subfix1 = getSourceBuildPhaseSource(sContent)
    prefix2,sources2,subfix2 = getSourceBuildPhaseSource(dContent)
    
    rsources1,rsources2 = resortSources(sources1, sources2)
    sContent = prefix1+sourcesToStr(rsources1)+subfix1
    dContent = prefix2+sourcesToStr(rsources2)+subfix2
    
#     print "sContent:\n%s\n\n\n" % sourcesToStr(rsources1)
#     print "dContent:\n%s\n" % sourcesToStr(rsources2)    
    return (sContent, dContent)

# 生成两个新的文件，主要对PBXBuildFile、PBXFileReference、PBXSourcesBuildPhase中的文件进行重新排序，方便使用第三方工具进行比较
def doDiff(sf,df):
    sContent = open(sf, "r").read()
    dContent = open(df, "r").read()
    
    sContent,dContent = doMergeBuildFile(sContent, dContent)
    sContent,dContent = doMergeFileReference(sContent, dContent)
    sContent,dContent = doMergeSourceBuildPhase(sContent, dContent)
    
    smf = sf+".merge"
    dmf = df+".merge"
    
    smfd = open(smf, 'w')
    smfd.write(sContent)
    smfd.close()
    
    dmfd = open(dmf, 'w')
    dmfd.write(dContent)
    dmfd.close()
    
    pass

# 对pbxproj文件进行简单检查，主要检查PBXBuildFile、PBXFileReference、PBXSourcesBuildPhase、PBXGroup中uuid的一致性
def doSimpleCheck(f):
    pass

def printUsage():
    usage = r'''Usage: python pbMerge.py file1 file2
    eg: python pbMerge.py 1.pbxproj 2.pbxproj
'''
    print usage
    pass

if __name__ == '__main__':
    if len(sys.argv)!=3:
        printUsage()
        exit(-1) 
    sf = sys.argv[1]
    df = sys.argv[2]
#     sf=r'''/work/workspace/diff/todo/project3.pbxproj'''
#     df=r'''/work/workspace/diff/todo/project4.pbxproj''
    doDiff(sf,df)
    
