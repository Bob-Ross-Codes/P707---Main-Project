using System.Collections.Generic;
using UnityEngine;
using Microsoft.Azure.Kinect.BodyTracking;

public class TrackerHandler2 : MonoBehaviour
{
    public Dictionary<JointId, JointId> parentJointMap;
    Dictionary<JointId, Quaternion> basisJointMap;

    // Up to 4 bodies tracked simultaneously
    public const int MAX_BODIES = 4;
    public Quaternion[][] multiBodyRotations = new Quaternion[MAX_BODIES][];
    public Vector3[] multiBodyPositions = new Vector3[MAX_BODIES];
    public bool[] bodyIsTracked = new bool[MAX_BODIES];

    // Kept for backward compatibility
    public Quaternion[] absoluteJointRotations = new Quaternion[(int)JointId.Count];
    public bool drawSkeletons = true;
    Quaternion Y_180_FLIP = new Quaternion(0.0f, 1.0f, 0.0f, 0.0f);

    void Awake()
    {
        for (int b = 0; b < MAX_BODIES; b++)
        {
            multiBodyRotations[b] = new Quaternion[(int)JointId.Count];
            bodyIsTracked[b] = false;
        }

        parentJointMap = new Dictionary<JointId, JointId>();
        parentJointMap[JointId.Pelvis] = JointId.Count;
        parentJointMap[JointId.SpineNavel] = JointId.Pelvis;
        parentJointMap[JointId.SpineChest] = JointId.SpineNavel;
        parentJointMap[JointId.Neck] = JointId.SpineChest;
        parentJointMap[JointId.ClavicleLeft] = JointId.SpineChest;
        parentJointMap[JointId.ShoulderLeft] = JointId.ClavicleLeft;
        parentJointMap[JointId.ElbowLeft] = JointId.ShoulderLeft;
        parentJointMap[JointId.WristLeft] = JointId.ElbowLeft;
        parentJointMap[JointId.HandLeft] = JointId.WristLeft;
        parentJointMap[JointId.HandTipLeft] = JointId.HandLeft;
        parentJointMap[JointId.ThumbLeft] = JointId.HandLeft;
        parentJointMap[JointId.ClavicleRight] = JointId.SpineChest;
        parentJointMap[JointId.ShoulderRight] = JointId.ClavicleRight;
        parentJointMap[JointId.ElbowRight] = JointId.ShoulderRight;
        parentJointMap[JointId.WristRight] = JointId.ElbowRight;
        parentJointMap[JointId.HandRight] = JointId.WristRight;
        parentJointMap[JointId.HandTipRight] = JointId.HandRight;
        parentJointMap[JointId.ThumbRight] = JointId.HandRight;
        parentJointMap[JointId.HipLeft] = JointId.SpineNavel;
        parentJointMap[JointId.KneeLeft] = JointId.HipLeft;
        parentJointMap[JointId.AnkleLeft] = JointId.KneeLeft;
        parentJointMap[JointId.FootLeft] = JointId.AnkleLeft;
        parentJointMap[JointId.HipRight] = JointId.SpineNavel;
        parentJointMap[JointId.KneeRight] = JointId.HipRight;
        parentJointMap[JointId.AnkleRight] = JointId.KneeRight;
        parentJointMap[JointId.FootRight] = JointId.AnkleRight;
        parentJointMap[JointId.Head] = JointId.Pelvis;
        parentJointMap[JointId.Nose] = JointId.Head;
        parentJointMap[JointId.EyeLeft] = JointId.Head;
        parentJointMap[JointId.EarLeft] = JointId.Head;
        parentJointMap[JointId.EyeRight] = JointId.Head;
        parentJointMap[JointId.EarRight] = JointId.Head;

        Vector3 zpositive = Vector3.forward;
        Vector3 xpositive = Vector3.right;
        Vector3 ypositive = Vector3.up;

        Quaternion leftHipBasis = Quaternion.LookRotation(xpositive, -zpositive);
        Quaternion spineHipBasis = Quaternion.LookRotation(xpositive, -zpositive);
        Quaternion rightHipBasis = Quaternion.LookRotation(xpositive, zpositive);
        Quaternion leftArmBasis = Quaternion.LookRotation(ypositive, -zpositive);
        Quaternion rightArmBasis = Quaternion.LookRotation(-ypositive, zpositive);
        Quaternion leftHandBasis = Quaternion.LookRotation(-zpositive, -ypositive);
        Quaternion rightHandBasis = Quaternion.identity;
        Quaternion leftFootBasis = Quaternion.LookRotation(xpositive, ypositive);
        Quaternion rightFootBasis = Quaternion.LookRotation(xpositive, -ypositive);

        basisJointMap = new Dictionary<JointId, Quaternion>();
        basisJointMap[JointId.Pelvis] = spineHipBasis;
        basisJointMap[JointId.SpineNavel] = spineHipBasis;
        basisJointMap[JointId.SpineChest] = spineHipBasis;
        basisJointMap[JointId.Neck] = spineHipBasis;
        basisJointMap[JointId.ClavicleLeft] = leftArmBasis;
        basisJointMap[JointId.ShoulderLeft] = leftArmBasis;
        basisJointMap[JointId.ElbowLeft] = leftArmBasis;
        basisJointMap[JointId.WristLeft] = leftHandBasis;
        basisJointMap[JointId.HandLeft] = leftHandBasis;
        basisJointMap[JointId.HandTipLeft] = leftHandBasis;
        basisJointMap[JointId.ThumbLeft] = leftArmBasis;
        basisJointMap[JointId.ClavicleRight] = rightArmBasis;
        basisJointMap[JointId.ShoulderRight] = rightArmBasis;
        basisJointMap[JointId.ElbowRight] = rightArmBasis;
        basisJointMap[JointId.WristRight] = rightHandBasis;
        basisJointMap[JointId.HandRight] = rightHandBasis;
        basisJointMap[JointId.HandTipRight] = rightHandBasis;
        basisJointMap[JointId.ThumbRight] = rightArmBasis;
        basisJointMap[JointId.HipLeft] = leftHipBasis;
        basisJointMap[JointId.KneeLeft] = leftHipBasis;
        basisJointMap[JointId.AnkleLeft] = leftHipBasis;
        basisJointMap[JointId.FootLeft] = leftFootBasis;
        basisJointMap[JointId.HipRight] = rightHipBasis;
        basisJointMap[JointId.KneeRight] = rightHipBasis;
        basisJointMap[JointId.AnkleRight] = rightHipBasis;
        basisJointMap[JointId.FootRight] = rightFootBasis;
        basisJointMap[JointId.Head] = spineHipBasis;
        basisJointMap[JointId.Nose] = spineHipBasis;
        basisJointMap[JointId.EyeLeft] = spineHipBasis;
        basisJointMap[JointId.EarLeft] = spineHipBasis;
        basisJointMap[JointId.EyeRight] = spineHipBasis;
        basisJointMap[JointId.EarRight] = spineHipBasis;
    }

    public void updateTracker(BackgroundData trackerFrameData)
    {
        for (int b = 0; b < MAX_BODIES; b++)
        {
            bodyIsTracked[b] = false;
        }

        int activeBodies = Mathf.Min((int)trackerFrameData.NumOfBodies, MAX_BODIES);

        for (int i = 0; i < activeBodies; i++)
        {
            Body skeleton = trackerFrameData.Bodies[i];
            bodyIsTracked[i] = true;

            // Cache pelvis translation for root positioning in camera space
            multiBodyPositions[i] = new Vector3(
                skeleton.JointPositions3D[(int)JointId.Pelvis].X,
                -skeleton.JointPositions3D[(int)JointId.Pelvis].Y,
                skeleton.JointPositions3D[(int)JointId.Pelvis].Z
            );

            // Compute joint orientations
            for (int jointNum = 0; jointNum < (int)JointId.Count; jointNum++)
            {
                Quaternion jointRot = Y_180_FLIP * new Quaternion(
                    skeleton.JointRotations[jointNum].X,
                    skeleton.JointRotations[jointNum].Y,
                    skeleton.JointRotations[jointNum].Z,
                    skeleton.JointRotations[jointNum].W
                ) * Quaternion.Inverse(basisJointMap[(JointId)jointNum]);

                multiBodyRotations[i][jointNum] = jointRot;

                if (i == 0)
                {
                    absoluteJointRotations[jointNum] = jointRot;
                }
            }

            // Draw visual stickman if child pointBody objects exist
            if (i < transform.childCount && drawSkeletons)
            {
                renderSkeleton(skeleton, i);
            }
        }
    }

    public void renderSkeleton(Body skeleton, int skeletonNumber)
    {
        for (int jointNum = 0; jointNum < (int)JointId.Count; jointNum++)
        {
            Vector3 jointPos = new Vector3(skeleton.JointPositions3D[jointNum].X, -skeleton.JointPositions3D[jointNum].Y, skeleton.JointPositions3D[jointNum].Z);
            Quaternion jointRot = multiBodyRotations[skeletonNumber][jointNum];

            Transform jointTransform = transform.GetChild(skeletonNumber).GetChild(jointNum);
            jointTransform.localPosition = jointPos;
            jointTransform.localRotation = jointRot;

            const int boneChildNum = 0;
            if (parentJointMap[(JointId)jointNum] != JointId.Head && parentJointMap[(JointId)jointNum] != JointId.Count)
            {
                Vector3 parentPos = new Vector3(
                    skeleton.JointPositions3D[(int)parentJointMap[(JointId)jointNum]].X,
                    -skeleton.JointPositions3D[(int)parentJointMap[(JointId)jointNum]].Y,
                    skeleton.JointPositions3D[(int)parentJointMap[(JointId)jointNum]].Z
                );
                Vector3 boneDirectionTrackerSpace = jointPos - parentPos;
                Vector3 boneDirectionWorldSpace = transform.rotation * boneDirectionTrackerSpace;
                Vector3 boneDirectionLocalSpace = Quaternion.Inverse(jointTransform.rotation) * Vector3.Normalize(boneDirectionWorldSpace);

                Transform boneTransform = jointTransform.GetChild(boneChildNum);
                boneTransform.localScale = new Vector3(1, 10.0f * boneDirectionWorldSpace.magnitude, 1);
                boneTransform.localRotation = Quaternion.FromToRotation(Vector3.up, boneDirectionLocalSpace);
                boneTransform.position = jointTransform.position - 0.5f * boneDirectionWorldSpace;
            }
            else
            {
                jointTransform.GetChild(boneChildNum).gameObject.SetActive(false);
            }
        }
    }
}