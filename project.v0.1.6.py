'''
Version - 0.1.3
Author - Pranay Meher   pranaymeher@gmail.com
Description - API plugin to create a project node which moves to the target position when the
value is set to 1. If it finds an intersection on the input mesh then the result position
is set on the collision point on the mesh

0.1.2 Update :
    Instead of connecting the worldMesh of the mesh now I'm taking the dagPath of the mesh
    to initialize the MFnMesh function set.

0.1.3 Update :
    Going back to the kMesh type for the mesh input instead of kString as it has updation issues
    instead of closestIntersection method, using allIntersection method as it is more stable

0.1.4 Update :
    Now the plugin respects the hierarchical transformation of the source and target objects.
    This is as good as using the inclusiveMatrix of the objects. Added a new function getTranslation()

0.1.5 Update:
    Changing the code to use new API 2.0

0.1.6 Update:
    Adding Rotation projection and dot product value of the hit face normal and the hit ray

'''
import sys
import maya.api.OpenMaya as OpenMaya
import math
#import maya.OpenMayaMPx as OpenMayaMPx

kNodeName = "projectNode"
kNodeId = OpenMaya.MTypeId(0x0007ffff)

def maya_useNewAPI():
    """
    Must be present for Maya to know it's using the new 2.0 api
    """
    pass

# Command
class project(OpenMaya.MPxNode):

    inputMatrix = OpenMaya.MObject()
    targetMatrix = OpenMaya.MObject()
    resultVector = OpenMaya.MObject()
    deltaVector = OpenMaya.MObject()
    value = OpenMaya.MObject()
    inMesh = OpenMaya.MObject()
    resultRotate = OpenMaya.MObject()
    dotProduct = OpenMaya.MObject()
    
    def __init__(self):
        OpenMaya.MPxNode.__init__(self)
        
    # Invoked when the command is run.
    def compute(self,plug,datahandle):
        if plug == self.resultVector or plug == self.resultRotate:
            datahandleinputMatrix = datahandle.inputValue(self.inputMatrix)
            datahandletargetMatrix = datahandle.inputValue(self.targetMatrix)
            datahandleValue = datahandle.inputValue(self.value)
            datahandleResultVector = datahandle.outputValue(self.resultVector)
            datahandleInMesh = datahandle.inputValue(self.inMesh)
            datahandleResultRotation = datahandle.outputValue(self.resultRotate)
            datahandleDotProduct = datahandle.outputValue(self.dotProduct)

            inputMatrixMatrix = datahandleinputMatrix.asMatrix()
            targetMatrixMatrix = datahandletargetMatrix.asMatrix()
            inputValue = datahandleValue.asFloat()
            inMeshGeom = datahandleInMesh.asMesh()

            inputMatrixValue = getTranslation(inputMatrixMatrix)
            targetMatrixValue = getTranslation(targetMatrixMatrix)

            deltaVector = (targetMatrixValue[0] - inputMatrixValue[0], targetMatrixValue[1] - inputMatrixValue[1], targetMatrixValue[2] - inputMatrixValue[2])
            dotProduct = 1.0
            rotation = [0, 0, 0]

            # Setting up variable for detecting collision using MFnMesh.closestIntersection method
            raySource = OpenMaya.MFloatPoint(inputMatrixValue[0], inputMatrixValue[1], inputMatrixValue[2])
            rayDirection = OpenMaya.MFloatVector(deltaVector[0], deltaVector[1], deltaVector[2])
            intersectionPoints = OpenMaya.MFloatPointArray()
            tolerance = 0.001

            # Creating and attaching MFnMesh
            mFnMesh = OpenMaya.MFnMesh(inMeshGeom)

            # Now calculating the intersection
            if not datahandleInMesh == None:
                hit = mFnMesh.allIntersections( raySource,                  # raySource - where we are shooting the ray from.
                                                rayDirection,               # rayDirection - the direction in which we are shooting the ray.
                                                OpenMaya.MSpace.kWorld,     # coordinate space - the mesh's local coordinate space.
                                                float(1),                   # max param the range of the ray.
                                                True,                      # testBothDirections - we are not checking both directions from the raySource
                                                #None,                       # faceIds - here, we do not care if specific faces are intersected)
                                                #None,                       # triIds - here, we do not care if specific tri's are intersected)
                                                #False,                      # idsSorted - here, we do not need to sort the faceId's or triId's indices.
                                                #None,                       # accelParams - this object is not applicable here.
                                                #tolerance,                  # tolerance
                                             )
                #print hit
                #print rayDirection

            # If intersection is detected then set the computedVector to the intersection point else set it to the delta value
            hitPoint, hitRayParam, hitFace, hitTriangle, hitBary1, hitBary2 = hit
            if hitPoint:
                deltaVector = (hitPoint[0].x - inputMatrixValue[0], hitPoint[0].y - inputMatrixValue[1], hitPoint[0].z - inputMatrixValue[2])
                
                # Now computing the result rotation
            
                # First getting the normal of the hit face
                faceNormal = mFnMesh.getPolygonNormal(hitFace[0], OpenMaya.MSpace.kWorld)

                # We already have the facenormal. Now storing the x and z vectors
                # of the input inputMatrix
                stdinX = OpenMaya.MVector(inputMatrixMatrix[0], inputMatrixMatrix[1], inputMatrixMatrix[2]).normal()
                stdinZ = OpenMaya.MVector(inputMatrixMatrix[8], inputMatrixMatrix[9], inputMatrixMatrix[10]).normal()

                # Making a binormal
                newX = faceNormal ^ stdinZ
                newZ = -faceNormal ^ newX
                newX = faceNormal ^ newZ

                newMatr = OpenMaya.MMatrix(((newX.x, newX.y, newX.z, 0),
                                (faceNormal.x, faceNormal.y, faceNormal.z, 0),
                                (newZ.x, newZ.y, newZ.z, 0),
                                (0, 0, 0, 1)))

                mFnMatrixData = OpenMaya.MFnMatrixData()
                mFnMatrixData.create( newMatr )
                worldMatrix = mFnMatrixData.transformation()
                rotation = worldMatrix.rotation(False)
    
                # Following commands converts the radian angles to degrees
                rotation = [math.degrees(angle) for angle in (rotation.x, rotation.y, rotation.z)]

                # Now computing the dot product between hit ray and the faceNormal
                hitRay = OpenMaya.MFloatPoint(raySource) - hitPoint[0]
                hitVect = OpenMaya.MFloatVector(hitRay)
                faceNormalVect = OpenMaya.MFloatVector(faceNormal)
                dotProduct = faceNormalVect * hitVect

            else:
                deltaVector = (targetMatrixValue[0] - inputMatrixValue[0], targetMatrixValue[1] - inputMatrixValue[1], targetMatrixValue[2] - inputMatrixValue[2])
                dotProduct = 1.0
                rotation = [0, 0, 0]
                
            computedVector = (deltaVector[0] * inputValue + inputMatrixValue[0], deltaVector[1] * inputValue + inputMatrixValue[1], deltaVector[2] * inputValue + inputMatrixValue[2])

            # Now flooding the output values in the node
            datahandleResultVector.set3Float(computedVector[0], computedVector[1], computedVector[2])
            datahandleResultRotation.set3Float(rotation[0], rotation[1], rotation[2])
            datahandleDotProduct.setFloat(dotProduct)



            datahandle.setClean(plug)

def getTranslation(matrix):
    # Creating TranformationMatrix with incoming matix
    mFnMatrixData = OpenMaya.MFnMatrixData()
    matrixMObject = mFnMatrixData.create( matrix )
    worldMatrix = mFnMatrixData.transformation()

    #mFnTransformMatrix = OpenMaya.MTransformationMatrix( worldMatrix )
    trans = worldMatrix.translation(OpenMaya.MSpace.kWorld)
    trans = [trans.x, trans.y, trans.z]
    #print trans
    #print type(trans)

    return trans

# Creator
def nodeCreator():
    return project()

def nodeInitializer():
    mFnNumericAttribute = OpenMaya.MFnNumericAttribute()
    mFnTypedAttribute = OpenMaya.MFnTypedAttribute()
    mFnMatrixAttribute = OpenMaya.MFnMatrixAttribute()

    project.inputMatrix = mFnMatrixAttribute.create("inputMatrix","inMat",OpenMaya.MFnMatrixAttribute.kDouble)
    mFnMatrixAttribute.readable = True 
    mFnMatrixAttribute.writable = True
    mFnMatrixAttribute.storable = True 
    #mFnMatrixAttribute.hidden(0)
    mFnMatrixAttribute.connectable = True 

    project.targetMatrix = mFnMatrixAttribute.create("targetMatrix","tarMat",OpenMaya.MFnMatrixAttribute.kDouble)
    mFnMatrixAttribute.readable = True
    mFnMatrixAttribute.writable = True
    mFnMatrixAttribute.storable = True
    #mFnMatrixAttribute.hidden(0)
    mFnMatrixAttribute.connectable = True

    project.deltaVector = mFnNumericAttribute.create("deltaVector","deltaVect",OpenMaya.MFnNumericData.k3Float)
    mFnNumericAttribute.readable = True
    mFnNumericAttribute.writable = False
    mFnNumericAttribute.storable = True
    mFnNumericAttribute.hidden = True
    mFnNumericAttribute.connectable = False

    project.resultVector = mFnNumericAttribute.create("resultVector","rsVect",OpenMaya.MFnNumericData.k3Float)
    mFnNumericAttribute.readable = True
    mFnNumericAttribute.writable = True
    mFnNumericAttribute.storable = True
    #mFnNumericAttribute.hidden(0)
    mFnNumericAttribute.connectable = True

    project.value = mFnNumericAttribute.create("value", "val", OpenMaya.MFnNumericData.kFloat,0.0)
    mFnNumericAttribute.readable = True
    mFnNumericAttribute.writable = True
    mFnNumericAttribute.keyable = True

    project.resultRotate = mFnNumericAttribute.create("resultRotate", "resRot", OpenMaya.MFnNumericData.k3Float)
    mFnNumericAttribute.readable = True
    mFnNumericAttribute.writable = True
    mFnNumericAttribute.storable = True
    #mFnNumericAttribute.hidden(0)
    mFnNumericAttribute.connectable = True

    project.dotProduct = mFnNumericAttribute.create("dotProduct", "dot", OpenMaya.MFnNumericData.kFloat, 0.0)
    mFnNumericAttribute.readable = True
    mFnNumericAttribute.writable = False
    mFnNumericAttribute.keyable = False
    mFnNumericAttribute.connectable = True

    project.inMesh = mFnTypedAttribute.create("inputMesh", "inMesh", OpenMaya.MFnData.kMesh)
    mFnTypedAttribute.readable = False


    project.addAttribute(project.inputMatrix)
    project.addAttribute(project.targetMatrix)
    project.addAttribute(project.resultVector)
    project.addAttribute(project.deltaVector)
    project.addAttribute(project.value)
    project.addAttribute(project.inMesh)
    project.addAttribute(project.resultRotate)
    project.addAttribute(project.dotProduct)

    project.attributeAffects(project.inputMatrix, project.resultVector)
    project.attributeAffects(project.targetMatrix, project.resultVector)
    project.attributeAffects(project.inputMatrix, project.resultRotate)
    project.attributeAffects(project.targetMatrix, project.resultRotate)
    project.attributeAffects(project.inMesh, project.resultRotate)
    project.attributeAffects(project.inputMatrix, project.dotProduct)
    project.attributeAffects(project.targetMatrix, project.dotProduct)
    project.attributeAffects(project.value, project.resultVector)
    project.attributeAffects(project.inMesh,project.resultVector)
    
# Initialize the script plug-in
def initializePlugin(mobject):
    mplugin = OpenMaya.MFnPlugin(mobject, 'Pranay Meher', '2.0')
    try:
        mplugin.registerNode( kNodeName, kNodeId, nodeCreator, nodeInitializer )
    except:
        sys.stderr.write( "Failed to register command: %s\n" % kNodeName )
        raise

# Uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = OpenMaya.MFnPlugin(mobject)
    try:
        mplugin.deregisterNode( kNodeName )
    except:
        sys.stderr.write( "Failed to unregister command: %s\n" % kNodeName )