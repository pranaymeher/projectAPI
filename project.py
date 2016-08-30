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

'''
import sys
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx

kNodeName = "projectNode"
kNodeId = OpenMaya.MTypeId(0x001273c0) # This is unique ID acquired from Autodesk

# Command
class project(OpenMayaMPx.MPxNode):

    inputMatrix = OpenMaya.MObject()
    targetMatrix = OpenMaya.MObject()
    resultPosition = OpenMaya.MObject()
    deltaVector = OpenMaya.MObject()
    value = OpenMaya.MObject()
    inMesh = OpenMaya.MObject()
    
    def __init__(self):
        OpenMayaMPx.MPxNode.__init__(self)
        
    # Invoked when the command is run.
    def compute(self,plug,datahandle):
        if plug == self.resultPosition:
            datahandleinputMatrix = datahandle.inputValue(self.inputMatrix)
            datahandletargetMatrix = datahandle.inputValue(self.targetMatrix)
            datahandleValue = datahandle.inputValue(self.value)
            datahandleresultPosition = datahandle.outputValue(self.resultPosition)
            datahandleInMesh = datahandle.inputValue(self.inMesh)

            inputMatrixMatrix = datahandleinputMatrix.asMatrix()
            targetMatrixMatrix = datahandletargetMatrix.asMatrix()
            inputValue = datahandleValue.asFloat()
            inMeshGeom = datahandleInMesh.asMesh()

            inputMatrixValue = getTranslation(inputMatrixMatrix)
            targetMatrixValue = getTranslation(targetMatrixMatrix)

            deltaVector = (targetMatrixValue[0] - inputMatrixValue[0], targetMatrixValue[1] - inputMatrixValue[1], targetMatrixValue[2] - inputMatrixValue[2])

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
                                                None,                       # faceIds - here, we do not care if specific faces are intersected)
                                                None,                       # triIds - here, we do not care if specific tri's are intersected)
                                                False,                      # idsSorted - here, we do not need to sort the faceId's or triId's indices.
                                                OpenMaya.MSpace.kWorld,     # coordinate space - the mesh's local coordinate space.
                                                float(1),                   # the range of the ray.
                                                False,                      # testBothDirections - we are not checking both directions from the raySource
                                                None,                       # accelParams - this object is not applicable here.
                                                False,                      # sortHits - we do not need to sort the intersection points along the ray.
                                                intersectionPoints,         # hitPoints - the array of points which have been intersected.
                                                None,                       # hitRayParams - we do not need any parametric distances of the points along the ray.
                                                None,                       # hitFaces - we do not need the id's of the faces intersected.
                                                None,                       # hitTriangles - we do not need the id's of the triangles intersected.
                                                None,                       # hitBary1s - we do not need the barycentric coordinates of the points within the triangles.
                                                None,                       # hitBary2s - we do not need the barycentric coordinates of the points within the triangles.
                                                tolerance                   # tolerance - a numeric tolerance threshold which allow intersections to occur just outside the mesh.
                                             )
                #print hit
                #print rayDirection

            # If intersection is detected then set the computedVector to the intersection point else set it to the delta value
            if hit:
                deltaVector = (intersectionPoints[0].x - inputMatrixValue[0], intersectionPoints[0].y - inputMatrixValue[1], intersectionPoints[0].z - inputMatrixValue[2])
            else:
                deltaVector = (targetMatrixValue[0] - inputMatrixValue[0], targetMatrixValue[1] - inputMatrixValue[1], targetMatrixValue[2] - inputMatrixValue[2])
                
            computedVector = (deltaVector[0] * inputValue + inputMatrixValue[0], deltaVector[1] * inputValue + inputMatrixValue[1], deltaVector[2] * inputValue + inputMatrixValue[2])
            datahandleresultPosition.set3Float(computedVector[0], computedVector[1], computedVector[2])

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
    return OpenMayaMPx.asMPxPtr( project() )

def nodeInitializer():
    mFnNumericAttribute = OpenMaya.MFnNumericAttribute()
    mFnTypedAttribute = OpenMaya.MFnTypedAttribute()
    mFnMatrixAttribute = OpenMaya.MFnMatrixAttribute()

    project.inputMatrix = mFnMatrixAttribute.create("inputMatrix","inMatr",OpenMaya.MFnMatrixAttribute.kDouble)
    mFnMatrixAttribute.setReadable(1)
    mFnMatrixAttribute.setWritable(1)
    mFnMatrixAttribute.setStorable(1)
    #mFnMatrixAttribute.setHidden(0)
    mFnMatrixAttribute.setConnectable(1)

    project.targetMatrix = mFnMatrixAttribute.create("targetMatrix","tarMatr",OpenMaya.MFnMatrixAttribute.kDouble)
    mFnMatrixAttribute.setReadable(1)
    mFnMatrixAttribute.setWritable(1)
    mFnMatrixAttribute.setStorable(1)
    #mFnMatrixAttribute.setHidden(0)
    mFnMatrixAttribute.setConnectable(1)

    project.deltaVector = mFnNumericAttribute.create("deltaVector","deltaVect",OpenMaya.MFnNumericData.k3Float)
    mFnNumericAttribute.setReadable(1)
    mFnNumericAttribute.setWritable(0)
    mFnNumericAttribute.setStorable(1)
    mFnNumericAttribute.setHidden(1)
    mFnNumericAttribute.setConnectable(0)

    project.resultPosition = mFnNumericAttribute.create("resultPosition","resPos",OpenMaya.MFnNumericData.k3Float)
    mFnNumericAttribute.setReadable(1)
    mFnNumericAttribute.setWritable(1)
    mFnNumericAttribute.setStorable(1)
    #mFnNumericAttribute.setHidden(0)
    mFnNumericAttribute.setConnectable(1)

    project.value = mFnNumericAttribute.create("value", "val", OpenMaya.MFnNumericData.kFloat,0.0)
    mFnNumericAttribute.setReadable(1)
    mFnNumericAttribute.setWritable(1)
    mFnNumericAttribute.setKeyable(1)

    project.inMesh = mFnTypedAttribute.create("inputMesh", "inMesh", OpenMaya.MFnData.kMesh)
    mFnTypedAttribute.setReadable(0)


    project.addAttribute(project.inputMatrix)
    project.addAttribute(project.targetMatrix)
    project.addAttribute(project.resultPosition)
    project.addAttribute(project.deltaVector)
    project.addAttribute(project.value)
    project.addAttribute(project.inMesh)

    project.attributeAffects(project.inputMatrix, project.resultPosition)
    project.attributeAffects(project.targetMatrix, project.resultPosition)
    project.attributeAffects(project.value, project.resultPosition)
    project.attributeAffects(project.inMesh,project.resultPosition)
    
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