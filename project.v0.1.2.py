'''
Version - 0.1.2
Author - Pranay Meher   pranaymeher@gmail.com
Description - API plugin to create a project node which moves to the target position when the
value is set to 1. If it finds an intersection on the input mesh then the result position
is set on the collision point on the mesh

0.1.2 Update :
    Instead of connecting the worldMesh of the mesh now I'm taking the dagPath of the mesh
    to initialize the MFnMesh function set.

'''

import sys
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx

kNodeName = "projectNode"
kNodeId = OpenMaya.MTypeId(0x0007ffff)


# Command
class project(OpenMayaMPx.MPxNode):

    inputVector = OpenMaya.MObject()
    targetVector = OpenMaya.MObject()
    resultVector = OpenMaya.MObject()
    deltaVector = OpenMaya.MObject()
    value = OpenMaya.MObject()
    inMesh = OpenMaya.MObject()
    
    def __init__(self):
        OpenMayaMPx.MPxNode.__init__(self)
        
    # Invoked when the command is run.
    def compute(self,plug,datahandle):
        if plug == self.resultVector:
            datahandleInputVector = datahandle.inputValue(self.inputVector)
            datahandleTargetVector = datahandle.inputValue(self.targetVector)
            datahandleValue = datahandle.inputValue(self.value)
            datahandleResultVector = datahandle.outputValue(self.resultVector)
            datahandleInMesh = datahandle.inputValue(self.inMesh)

            inputVectorValue = datahandleInputVector.asFloat3()
            targetVectorValue = datahandleTargetVector.asFloat3()
            inputValue = datahandleValue.asFloat()
            inMeshGeom = datahandleInMesh.asString()


            deltaVector = (targetVectorValue[0] - inputVectorValue[0], targetVectorValue[1] - inputVectorValue[1], targetVectorValue[2] - inputVectorValue[2])

            # Setting up variable for detecting collision using MFnMesh.closestIntersection method
            raySource = OpenMaya.MFloatPoint(inputVectorValue[0], inputVectorValue[1], inputVectorValue[2])
            rayDirection = OpenMaya.MFloatVector(deltaVector[0], deltaVector[1], deltaVector[2])
            space = OpenMaya.MSpace.kWorld
            maxParam = float(1)
            testBothDirection = False
            faceIds = None 
            triIds = None 
            idsSorted = False
            accelParams = None
            tolerence = None
            hitPoint = OpenMaya.MFloatPoint()
            hitRayParam = None
            hitFacePtr = OpenMaya.MScriptUtil().asIntPtr()
            hitTriangle = None
            hitBary1 = None
            hitBary2 = None

            # Creating and attaching MFnMesh
            selList = OpenMaya.MSelectionList()
            selList.clear()
            selList.add( inMeshGeom )
            meshDagPath = OpenMaya.MDagPath()  # Storage for mesh transform dag path
            selList.getDagPath( 0,  meshDagPath )
            meshDagPath.extendToShape()
            mFnMesh = OpenMaya.MFnMesh(meshDagPath)

            # Now calculating the intersection
            if not datahandleInMesh == None:
                hit = mFnMesh.closestIntersection(raySource,
                                                rayDirection,
                                                faceIds,
                                                triIds,
                                                idsSorted,
                                                space,
                                                maxParam,
                                                testBothDirection,
                                                accelParams,
                                                hitPoint,
                                                hitRayParam,
                                                hitFacePtr,
                                                hitTriangle,
                                                hitBary1,
                                                hitBary2)
                #print hit
                #print rayDirection

            # If intersection is detected then set the computedVector to the intersection point else set it to the delta value
            if hit:
                deltaVector = (hitPoint.x - inputVectorValue[0], hitPoint.y - inputVectorValue[1], hitPoint.z - inputVectorValue[2])
            else:
                deltaVector = (targetVectorValue[0] - inputVectorValue[0], targetVectorValue[1] - inputVectorValue[1], targetVectorValue[2] - inputVectorValue[2])
                
            computedVector = (deltaVector[0] * inputValue + inputVectorValue[0], deltaVector[1] * inputValue + inputVectorValue[1], deltaVector[2] * inputValue + inputVectorValue[2])
            datahandleResultVector.set3Float(computedVector[0], computedVector[1], computedVector[2])

            datahandle.setClean(plug)

# Creator
def nodeCreator():
    return OpenMayaMPx.asMPxPtr( project() )

def nodeInitializer():
    mFnNumericAttribute = OpenMaya.MFnNumericAttribute()
    mFnTypedAttribute = OpenMaya.MFnTypedAttribute()

    project.inputVector = mFnNumericAttribute.create("inputVector","inVect",OpenMaya.MFnNumericData.k3Float)
    mFnNumericAttribute.setReadable(1)
    mFnNumericAttribute.setWritable(1)
    mFnNumericAttribute.setStorable(1)
    #mFnNumericAttribute.setHidden(0)
    mFnNumericAttribute.setConnectable(1)

    project.targetVector = mFnNumericAttribute.create("targetVector","tarVect",OpenMaya.MFnNumericData.k3Float)
    mFnNumericAttribute.setReadable(1)
    mFnNumericAttribute.setWritable(1)
    mFnNumericAttribute.setStorable(1)
    #mFnNumericAttribute.setHidden(0)
    mFnNumericAttribute.setConnectable(1)

    project.deltaVector = mFnNumericAttribute.create("deltaVector","deltaVect",OpenMaya.MFnNumericData.k3Float)
    mFnNumericAttribute.setReadable(1)
    mFnNumericAttribute.setWritable(0)
    mFnNumericAttribute.setStorable(1)
    mFnNumericAttribute.setHidden(1)
    mFnNumericAttribute.setConnectable(0)

    project.resultVector = mFnNumericAttribute.create("resultVector","rsVect",OpenMaya.MFnNumericData.k3Float)
    mFnNumericAttribute.setReadable(1)
    mFnNumericAttribute.setWritable(1)
    mFnNumericAttribute.setStorable(1)
    #mFnNumericAttribute.setHidden(0)
    mFnNumericAttribute.setConnectable(1)

    project.value = mFnNumericAttribute.create("value", "val", OpenMaya.MFnNumericData.kFloat,0.0)
    mFnNumericAttribute.setReadable(1)
    mFnNumericAttribute.setWritable(1)
    mFnNumericAttribute.setKeyable(1)

    project.inMesh = mFnTypedAttribute.create("inputMesh", "inMesh", OpenMaya.MFnData.kString)
    mFnTypedAttribute.setReadable(1)
    mFnTypedAttribute.setWritable(1)
    mFnNumericAttribute.setStorable(1)


    project.addAttribute(project.inputVector)
    project.addAttribute(project.targetVector)
    project.addAttribute(project.resultVector)
    project.addAttribute(project.deltaVector)
    project.addAttribute(project.value)
    project.addAttribute(project.inMesh)

    project.attributeAffects(project.inputVector, project.resultVector)
    project.attributeAffects(project.targetVector, project.resultVector)
    project.attributeAffects(project.value, project.resultVector)
    project.attributeAffects(project.inMesh,project.resultVector)
    
# Initialize the script plug-in
def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.registerNode( kNodeName, kNodeId, nodeCreator, nodeInitializer )
    except:
        sys.stderr.write( "Failed to register command: %s\n" % kNodeName )
        raise

# Uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode( kNodeName )
    except:
        sys.stderr.write( "Failed to unregister command: %s\n" % kNodeName )