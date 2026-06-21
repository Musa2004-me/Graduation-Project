using UnityEngine;
public class FollowRotationOnly : MonoBehaviour 
{ 
	public Transform wheel;
	void LateUpdate() 
	{ transform.rotation = wheel.rotation; } 
}
