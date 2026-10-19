using System.Collections.Generic;
using UnityEngine;
using Microsoft.Azure.Kinect.BodyTracking;
using System.Text;

public class PuppetAvatar2 : MonoBehaviour
{
    [Header("Tracker Reference")]
    public TrackerHandler2 KinectDevice;

    [Header("Multi-user Settings")]
    [Tooltip("0 = First person detected, 1 = Second person detected")]
    public int bodyIndex = 0;

    [Header("Position Offsets")]
    public Transform CharacterRootTransform;
    public float OffsetY = 0f;
    public float OffsetZ = 0f;

    [Header("Smoothing Settings")]
    [Tooltip("Smoothing speed for body position (higher = faster response, lower = smoother). Range: 10 - 25 recommended.")]
    [Range(1f, 50f)]
    public float positionSmoothing = 18f;

    [Tooltip("Smoothing speed for joint rotations (higher = faster response, lower = smoother). Range: 15 - 30 recommended.")]
    [Range(1f, 50f)]
    public float rotationSmoothing = 20f;

    Dictionary<JointId, Quaternion> absoluteOffsetMap;
    Animator PuppetAnimator;

    // Cache smoothed states per joint
    private Quaternion[] smoothedRotations = new Quaternion[(int)JointId.Count];
    private Vector3 smoothedPelvisPosition;
    private bool initializedSmoothing = false;

    private static HumanBodyBones MapKinectJoint(JointId joint)
    {
        switch (joint)
        {
            case JointId.Pelvis: return HumanBodyBones.Hips;
            case JointId.SpineNavel: return HumanBodyBones.Spine;
            case JointId.SpineChest: return HumanBodyBones.Chest;
            case JointId.Neck: return HumanBodyBones.Neck;
            case JointId.Head: return HumanBodyBones.Head;
            case JointId.HipLeft: return HumanBodyBones.LeftUpperLeg;
            case JointId.KneeLeft: return HumanBodyBones.LeftLowerLeg;
            case JointId.AnkleLeft: return HumanBodyBones.LeftFoot;
            case JointId.FootLeft: return HumanBodyBones.LeftToes;
            case JointId.HipRight: return HumanBodyBones.RightUpperLeg;
            case JointId.KneeRight: return HumanBodyBones.RightLowerLeg;
            case JointId.AnkleRight: return HumanBodyBones.RightFoot;
            case JointId.FootRight: return HumanBodyBones.RightToes;
            case JointId.ClavicleLeft: return HumanBodyBones.LeftShoulder;
            case JointId.ShoulderLeft: return HumanBodyBones.LeftUpperArm;
            case JointId.ElbowLeft: return HumanBodyBones.LeftLowerArm;
            case JointId.WristLeft: return HumanBodyBones.LeftHand;
            case JointId.ClavicleRight: return HumanBodyBones.RightShoulder;
            case JointId.ShoulderRight: return HumanBodyBones.RightUpperArm;
            case JointId.ElbowRight: return HumanBodyBones.RightLowerArm;
            case JointId.WristRight: return HumanBodyBones.RightHand;
            default: return HumanBodyBones.LastBone;
        }
    }

    private void Start()
    {
        PuppetAnimator = GetComponent<Animator>();
        Transform _rootJointTransform = CharacterRootTransform != null ? CharacterRootTransform : transform;

        absoluteOffsetMap = new Dictionary<JointId, Quaternion>();
        for (int i = 0; i < (int)JointId.Count; i++)
        {
            HumanBodyBones hbb = MapKinectJoint((JointId)i);
            if (hbb != HumanBodyBones.LastBone)
            {
                Transform boneTransform = PuppetAnimator.GetBoneTransform(hbb);
                if (boneTransform != null)
                {
                    Quaternion absOffset = GetSkeletonBone(PuppetAnimator, boneTransform.name).rotation;
                    Transform current = boneTransform;
                    while (!ReferenceEquals(current, _rootJointTransform) && current.parent != null)
                    {
                        current = current.parent;
                        absOffset = GetSkeletonBone(PuppetAnimator, current.name).rotation * absOffset;
                    }
                    absoluteOffsetMap[(JointId)i] = absOffset;
                }
            }
        }
    }

    private static SkeletonBone GetSkeletonBone(Animator animator, string boneName)
    {
        int count = 0;
        StringBuilder cloneName = new StringBuilder(boneName);
        cloneName.Append("(Clone)");
        foreach (SkeletonBone sb in animator.avatar.humanDescription.skeleton)
        {
            if (sb.name == boneName || sb.name == cloneName.ToString())
            {
                return animator.avatar.humanDescription.skeleton[count];
            }
            count++;
        }
        return new SkeletonBone();
    }

    private void LateUpdate()
    {
        if (KinectDevice == null || bodyIndex >= TrackerHandler2.MAX_BODIES || !KinectDevice.bodyIsTracked[bodyIndex])
        {
            // Reset initialization flag so entering the frame snaps immediately instead of sliding across the room
            initializedSmoothing = false;
            return;
        }

        Vector3 rootPosKinect = KinectDevice.multiBodyPositions[bodyIndex];
        Vector3 originPos = CharacterRootTransform != null ? CharacterRootTransform.position : transform.position;

        // Calculate target pelvis world position
        Vector3 targetPelvisPos = originPos + new Vector3(
            rootPosKinect.x,
            rootPosKinect.y + OffsetY,
            rootPosKinect.z - OffsetZ
        );

        // Snap on first frame detected, then smooth
        if (!initializedSmoothing)
        {
            smoothedPelvisPosition = targetPelvisPos;
            for (int k = 0; k < (int)JointId.Count; k++)
            {
                smoothedRotations[k] = KinectDevice.multiBodyRotations[bodyIndex][k];
            }
            initializedSmoothing = true;
        }
        else
        {
            float posLerpFactor = 1f - Mathf.Exp(-positionSmoothing * Time.deltaTime);
            smoothedPelvisPosition = Vector3.Lerp(smoothedPelvisPosition, targetPelvisPos, posLerpFactor);
        }

        float rotLerpFactor = 1f - Mathf.Exp(-rotationSmoothing * Time.deltaTime);

        for (int j = 0; j < (int)JointId.Count; j++)
        {
            HumanBodyBones hbb = MapKinectJoint((JointId)j);
            if (hbb != HumanBodyBones.LastBone && absoluteOffsetMap.ContainsKey((JointId)j))
            {
                Quaternion absOffset = absoluteOffsetMap[(JointId)j];
                Transform finalJoint = PuppetAnimator.GetBoneTransform(hbb);

                if (finalJoint != null)
                {
                    // Interpolate rotations smoothly using Slerp
                    Quaternion rawRot = KinectDevice.multiBodyRotations[bodyIndex][j];
                    smoothedRotations[j] = Quaternion.Slerp(smoothedRotations[j], rawRot, rotLerpFactor);

                    finalJoint.rotation = absOffset * Quaternion.Inverse(absOffset) * smoothedRotations[j] * absOffset;

                    // Pelvis / Hips position
                    if (j == 0)
                    {
                        finalJoint.position = smoothedPelvisPosition;
                    }
                }
            }
        }
    }
}