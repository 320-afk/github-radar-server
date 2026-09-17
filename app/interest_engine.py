"""Engine for calculating user interest vectors based on feedback history."""

from typing import Dict, List, Any

from .cache import repo_cache


def compute_interest_vector(feedback_log: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes language and topic weights from the feedback log.
    
    Weights:
    LIKE/SAVE/TRIED/DEPLOYED = +1.0
    NOT_INTERESTED = -0.5
    TOO_MANY = -0.3
    """
    language_weights: Dict[str, float] = {}
    topic_weights: Dict[str, float] = {}
    feedback_counts: Dict[str, int] = {}
    
    for entry in feedback_log:
        repo_id = entry.get("repo_id")
        action = entry.get("action")
        
        if not repo_id or not action:
            continue
            
        feedback_counts[action] = feedback_counts.get(action, 0) + 1
        
        weight = 0.0
        if action in ("like", "save", "TRIED", "DEPLOYED"):
            weight = 1.0
        elif action == "NOT_INTERESTED":
            weight = -0.5
        elif action == "TOO_MANY":
            weight = -0.3
            
        if weight == 0.0:
            continue
            
        repo = repo_cache.get(repo_id)
        if not repo:
            continue
            
        # Apply weight to language
        if repo.language:
            language_weights[repo.language] = language_weights.get(repo.language, 0.0) + weight
            
        # Apply weight to topics
        for topic in repo.topics:
            topic_weights[topic] = topic_weights.get(topic, 0.0) + weight
            
    return {
        "language_weights": language_weights,
        "topic_weights": topic_weights,
        "feedback_counts": feedback_counts,
    }
