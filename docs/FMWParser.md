# Introduction


<img src="https://lh3.googleusercontent.com/Tjiw0veAqclg1fiFQBVwb7Z4SUv1mQReLzMlVKYHxZnbUoAygOsOAiwF9k_tWal_nIPVaaK72DnsL7hWQzvzJtuG0vw25zh7LEFoCbcU7Vr10dRVk-XgjM3c9YMS89fpE-N0ahl5E4U989_-JhrDl3WtPqAmoL2BRl_cSqK2Up_xH9zMnK_0iErPjBMYQAaEqLoMF2C6hdadZwM10ASUyvQtYgzGbv3fh47zlnAh6XtCV-Yf3XX9OniiX3mjWAj0TgD3pU6hSQasZtSTyWKq6FiLb2uNPHZflFkLWf-PuBCnw38d2vn0n1SkbgzwcX0il4J1XIHxyfd6b3KayYPgzmCoji1u6OnJ26yILY0bID6Guahx-J-dXTLfD-xgskBnafyAznnq8wWkp6i4CrrML3QgbAVSuCxePgaNGlGgNDn2c4v008QoZrccpTPX3bxeogQ_ZgswTK1wV0I_jGmkTfWmfbFm17t_teLMC8fWiZGgbu6Slhm1dyGnhr27Zdn_HU1sACpawkTBH6y__8rFsYtY3VjqVmamSRGslqMfYO0sYw_ntZCc319FElNa2ARfYSTihxKta9HnRKpiJtfo5GjBbY8snTCoKxi588ibwaqJvnaiQ-M39ZoUwRLofEUwoHGqElExaNAMBpJg5o8uNZ4J5rPpDvFH1Q=w1508-h848-no" width="600"/>

Intent of this document is to describe the FMWParser library to 
hopefully allow easy parsing of FMW documents.  This library is 
currently a work in progress.  Demo code shown below shows what 
currently works and also provides a structure where future functionality 
would go.

Most objects that make up the 'workspace' object have a getJson object.
These functions work but the output will change.  When I have time the 
intent is that these methods will return all the information about a 
particular object that came from the FMW xml.  Ie all the information 
there as a json struct.

# Getting Started:

## Object Hierarchy

The parser breaks an FMW document up into the following components:
 - Workspace
    - Feature Classes
        - Sources
        - Destinations
    - Transformers
    - Published Parameters
    
The indentation reflects the object model structure.  Based on the bullets
above you can correctly infer that you start with a Workspace, from a 
workspace you can retrieve Feature Classes, Transformers and Published 
Parameters.

## Examples:

### Getting the workspace name
To retrieve a workspace name you need to:
1. create a parser
2. get a workspace object
3. get the workspace objects name

``` python
import FMEUtil.FMWParser
fmwFile = r'C:\somePath\to\my\fmws\test.fmw'
parser = FMEUtil.FMWParser.FMWParser(fmwFile)
wrkspcObj = parser.getFMEWorkspace()
wrkspaceName = wrkspcObj.getWorkspaceName()
print 'wrkspaceName', wrkspaceName
```

### Getting the sources

Steps illustrated in code:
1. create the parser
2. get a workspace object
3. from the workspace get the feature classes
4. from feature classes get the sources
5. iterate over the sources printing the source name
6. for each source get the dataset
7. from the dataset get the dataset name.

``` python
import FMEUtil.FMWParser
parser = FMEUtil.FMWParser.FMWParser(self.fmwFile)

wrkspcObj = parser.getFMEWorkspace()
featureClasses = wrkspcObj.getFeatureClasses()
sources = featureClasses.getSources()
for src in sources:
    print 'src:', src.getFeatureClassName()
    print 'dataset', src.getDataSet().getDataSetName()
```


and the same thing for destinations:

``` python
...
dests = featureClasses.getDestinations()
for dest in dests:
    print 'dest:', dest.getFeatureClassName()
    print 'dataset:', dest.getFeatureClassName()
```

For more examples see the FMWParserGettingStartedDemo.py file in the 
FMEUtil repo.

