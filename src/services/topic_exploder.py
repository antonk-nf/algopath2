"""Topic explosion system for handling comma-separated topics."""

import logging
import pandas as pd
import re
from typing import List, Tuple, Dict, Any, Optional

from src.models.data_models import ValidationResult


logger = logging.getLogger(__name__)


class TopicExploder:
    """Handles explosion of comma-separated topics into individual records."""
    
    # Common topic name variations and their standardized forms
    TOPIC_STANDARDIZATION = {
        # Data structures
        'array': 'Array',
        'arrays': 'Array',
        'string': 'String',
        'strings': 'String',
        'linked list': 'Linked List',
        'linkedlist': 'Linked List',
        'tree': 'Tree',
        'trees': 'Tree',
        'binary tree': 'Binary Tree',
        'bst': 'Binary Search Tree',
        'binary search tree': 'Binary Search Tree',
        'heap': 'Heap',
        'priority queue': 'Heap',
        'stack': 'Stack',
        'queue': 'Queue',
        'hash table': 'Hash Table',
        'hashtable': 'Hash Table',
        'hashmap': 'Hash Table',
        'hash map': 'Hash Table',
        'graph': 'Graph',
        'graphs': 'Graph',
        'trie': 'Trie',
        'prefix tree': 'Trie',
        
        # Algorithms
        'dfs': 'Depth-First Search',
        'depth first search': 'Depth-First Search',
        'depth-first search': 'Depth-First Search',
        'bfs': 'Breadth-First Search',
        'breadth first search': 'Breadth-First Search',
        'breadth-first search': 'Breadth-First Search',
        'binary search': 'Binary Search',
        'two pointers': 'Two Pointers',
        'two pointer': 'Two Pointers',
        'sliding window': 'Sliding Window',
        'dynamic programming': 'Dynamic Programming',
        'dp': 'Dynamic Programming',
        'greedy': 'Greedy',
        'backtracking': 'Backtracking',
        'recursion': 'Recursion',
        'divide and conquer': 'Divide and Conquer',
        'sorting': 'Sorting',
        'sort': 'Sorting',
        
        # Math and logic
        'math': 'Math',
        'mathematics': 'Math',
        'bit manipulation': 'Bit Manipulation',
        'bitwise': 'Bit Manipulation',
        'simulation': 'Simulation',
        'brainteaser': 'Brainteaser',
        'brain teaser': 'Brainteaser',
        
        # Design patterns
        'design': 'Design',
        'system design': 'Design',
        'oop': 'Design',
        'object oriented': 'Design',
        
        # Database
        'database': 'Database',
        'sql': 'Database',
        
        # Concurrency
        'concurrency': 'Concurrency',
        'multithreading': 'Concurrency',
        'multi-threading': 'Concurrency',
        'thread': 'Concurrency',
    }
    
    def __init__(self, standardize_topics: bool = True):
        """Initialize the topic exploder.
        
        Args:
            standardize_topics: Whether to standardize topic names
        """
        self.standardize_topics = standardize_topics
    
    def explode_topics(self, df: pd.DataFrame, topics_column: str = 'topics') -> Tuple[pd.DataFrame, ValidationResult]:
        """Explode comma-separated topics into individual records.
        
        Args:
            df: Input DataFrame with topics column
            topics_column: Name of the column containing comma-separated topics
            
        Returns:
            Tuple of (exploded DataFrame, validation result)
        """
        if df.empty:
            return df, ValidationResult(
                is_valid=True,
                errors=[],
                warnings=["DataFrame is empty"],
                processed_rows=0,
                skipped_rows=0
            )
        
        if topics_column not in df.columns:
            error_msg = f"Topics column '{topics_column}' not found in DataFrame"
            logger.error(error_msg)
            return df, ValidationResult(
                is_valid=False,
                errors=[error_msg],
                warnings=[],
                processed_rows=0,
                skipped_rows=0
            )
        
        logger.info(f"Exploding topics for {len(df)} rows")
        
        errors = []
        warnings = []
        original_rows = len(df)
        
        try:
            # Create a copy to avoid modifying the original
            exploded_df = df.copy()
            
            # Clean and split topics
            exploded_df[topics_column] = exploded_df[topics_column].apply(self._clean_and_split_topics)
            
            # Explode the topics column
            exploded_df = exploded_df.explode(topics_column, ignore_index=True)
            
            # Remove rows with empty topics
            before_cleanup = len(exploded_df)
            exploded_df = exploded_df[exploded_df[topics_column].notna()]
            exploded_df = exploded_df[exploded_df[topics_column].str.strip() != '']
            after_cleanup = len(exploded_df)
            
            removed_rows = before_cleanup - after_cleanup
            if removed_rows > 0:
                warnings.append(f"Removed {removed_rows} rows with empty topics")
            
            # Standardize topic names if requested
            if self.standardize_topics:
                exploded_df[topics_column] = exploded_df[topics_column].apply(self._standardize_topic)
            
            # Add topic metadata
            exploded_df = self._add_topic_metadata(exploded_df, topics_column)
            
            logger.info(f"Topic explosion complete: {original_rows} -> {len(exploded_df)} rows")
            
        except Exception as e:
            error_msg = f"Error during topic explosion: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            exploded_df = df  # Return original on error
        
        validation_result = ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            processed_rows=len(exploded_df),
            skipped_rows=original_rows - len(exploded_df) if len(errors) == 0 else 0
        )
        
        return exploded_df, validation_result
    
    def create_both_views(self, df: pd.DataFrame, topics_column: str = 'topics') -> Tuple[pd.DataFrame, pd.DataFrame, ValidationResult]:
        """Create both exploded and non-exploded views of the data.
        
        Args:
            df: Input DataFrame with topics column
            topics_column: Name of the column containing comma-separated topics
            
        Returns:
            Tuple of (non-exploded DataFrame, exploded DataFrame, validation result)
        """
        if df.empty:
            return df, df, ValidationResult(
                is_valid=True,
                errors=[],
                warnings=["DataFrame is empty"],
                processed_rows=0,
                skipped_rows=0
            )
        
        logger.info("Creating both exploded and non-exploded views")
        
        # Create non-exploded view (cleaned but not exploded)
        non_exploded_df = df.copy()
        errors = []
        warnings = []
        
        try:
            # Clean topics in non-exploded view
            if topics_column in non_exploded_df.columns:
                non_exploded_df[topics_column] = non_exploded_df[topics_column].apply(
                    lambda x: self._clean_topics_string(x) if pd.notna(x) else ''
                )
                
                # Add topic count metadata
                non_exploded_df['topic_count'] = non_exploded_df[topics_column].apply(
                    lambda x: len([t.strip() for t in str(x).split(',') if t.strip()]) if x else 0
                )
            
            # Create exploded view
            exploded_df, explosion_result = self.explode_topics(df, topics_column)
            
            # Combine validation results
            errors.extend(explosion_result.errors)
            warnings.extend(explosion_result.warnings)
            
        except Exception as e:
            error_msg = f"Error creating both views: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            exploded_df = df
        
        validation_result = ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            processed_rows=len(non_exploded_df),
            skipped_rows=0
        )
        
        return non_exploded_df, exploded_df, validation_result
    
    def _clean_and_split_topics(self, topics_value: Any) -> List[str]:
        """Clean and split a topics string into a list of individual topics.
        
        Args:
            topics_value: Raw topics value (could be string, NaN, etc.)
            
        Returns:
            List of cleaned topic strings
        """
        if pd.isna(topics_value) or topics_value == '':
            return []
        
        topics_str = str(topics_value).strip()
        if not topics_str:
            return []
        
        # Split by comma and clean each topic
        topics = []
        for topic in topics_str.split(','):
            cleaned_topic = topic.strip()
            if cleaned_topic:
                topics.append(cleaned_topic)
        
        return topics
    
    def _clean_topics_string(self, topics_value: Any) -> str:
        """Clean a topics string without splitting it.
        
        Args:
            topics_value: Raw topics value
            
        Returns:
            Cleaned topics string
        """
        if pd.isna(topics_value) or topics_value == '':
            return ''
        
        topics_str = str(topics_value).strip()
        if not topics_str:
            return ''
        
        # Split, clean, and rejoin
        topics = []
        for topic in topics_str.split(','):
            cleaned_topic = topic.strip()
            if cleaned_topic:
                if self.standardize_topics:
                    cleaned_topic = self._standardize_topic(cleaned_topic)
                topics.append(cleaned_topic)
        
        return ', '.join(topics)
    
    def _standardize_topic(self, topic: str) -> str:
        """Standardize a topic name.
        
        Args:
            topic: Raw topic name
            
        Returns:
            Standardized topic name
        """
        if not topic or pd.isna(topic):
            return topic
        
        topic_lower = str(topic).lower().strip()
        
        # Check for exact matches first
        if topic_lower in self.TOPIC_STANDARDIZATION:
            return self.TOPIC_STANDARDIZATION[topic_lower]
        
        # Check for partial matches (for compound topics)
        for key, standardized in self.TOPIC_STANDARDIZATION.items():
            if key in topic_lower:
                # Replace the matched part with standardized version
                return topic_lower.replace(key, standardized).title()
        
        # If no match found, return title case version
        return topic.strip().title()
    
    def _add_topic_metadata(self, df: pd.DataFrame, topics_column: str) -> pd.DataFrame:
        """Add metadata about topics to the DataFrame.
        
        Args:
            df: DataFrame with exploded topics
            topics_column: Name of the topics column
            
        Returns:
            DataFrame with additional topic metadata
        """
        # Add topic length
        df['topic_length'] = df[topics_column].str.len()
        
        # Add topic category (basic categorization)
        df['topic_category'] = df[topics_column].apply(self._categorize_topic)
        
        # Add topic complexity indicator (basic heuristic)
        df['topic_complexity'] = df[topics_column].apply(self._estimate_topic_complexity)
        
        return df
    
    def _categorize_topic(self, topic: str) -> str:
        """Categorize a topic into a broader category.
        
        Args:
            topic: Topic name
            
        Returns:
            Topic category
        """
        if not topic or pd.isna(topic):
            return 'unknown'
        
        topic_lower = str(topic).lower()
        
        # Data structures
        data_structures = ['array', 'string', 'linked list', 'tree', 'heap', 'stack', 
                          'queue', 'hash', 'graph', 'trie']
        if any(ds in topic_lower for ds in data_structures):
            return 'data_structure'
        
        # Algorithms
        algorithms = ['search', 'sort', 'dynamic programming', 'greedy', 'backtrack', 
                     'recursion', 'divide', 'two pointer', 'sliding window']
        if any(algo in topic_lower for algo in algorithms):
            return 'algorithm'
        
        # Math
        math_topics = ['math', 'bit manipulation', 'number', 'geometry']
        if any(math in topic_lower for math in math_topics):
            return 'math'
        
        # System design
        design_topics = ['design', 'system', 'oop', 'concurrency']
        if any(design in topic_lower for design in design_topics):
            return 'design'
        
        # Database
        if 'database' in topic_lower or 'sql' in topic_lower:
            return 'database'
        
        return 'other'
    
    def _estimate_topic_complexity(self, topic: str) -> str:
        """Estimate the complexity level of a topic (basic heuristic).
        
        Args:
            topic: Topic name
            
        Returns:
            Complexity level ('basic', 'intermediate', 'advanced')
        """
        if not topic or pd.isna(topic):
            return 'unknown'
        
        topic_lower = str(topic).lower()
        
        # Advanced topics
        advanced_topics = ['dynamic programming', 'backtracking', 'divide and conquer',
                          'trie', 'segment tree', 'binary indexed tree', 'union find',
                          'topological sort', 'minimum spanning tree', 'shortest path']
        if any(adv in topic_lower for adv in advanced_topics):
            return 'advanced'
        
        # Intermediate topics
        intermediate_topics = ['binary search', 'two pointers', 'sliding window',
                              'depth-first search', 'breadth-first search', 'heap',
                              'binary tree', 'graph', 'recursion']
        if any(inter in topic_lower for inter in intermediate_topics):
            return 'intermediate'
        
        # Basic topics (default for common data structures)
        return 'basic'
    
    def get_topic_statistics(self, df: pd.DataFrame, topics_column: str = 'topics') -> Dict[str, Any]:
        """Get statistics about topics in the DataFrame.
        
        Args:
            df: DataFrame with topics (exploded or non-exploded)
            topics_column: Name of the topics column
            
        Returns:
            Dictionary with topic statistics
        """
        stats = {}
        
        if df.empty or topics_column not in df.columns:
            return {'message': 'No topic data available'}
        
        # Check if this is exploded data (one topic per row) or non-exploded (comma-separated)
        is_exploded = not df[topics_column].str.contains(',', na=False).any()
        
        if is_exploded:
            # Statistics for exploded data
            stats['total_topic_records'] = len(df)
            stats['unique_topics'] = df[topics_column].nunique()
            stats['most_common_topics'] = df[topics_column].value_counts().head(20).to_dict()
            
            if 'topic_category' in df.columns:
                stats['topic_categories'] = df['topic_category'].value_counts().to_dict()
            
            if 'topic_complexity' in df.columns:
                stats['complexity_distribution'] = df['topic_complexity'].value_counts().to_dict()
                
        else:
            # Statistics for non-exploded data
            stats['total_problems'] = len(df)
            
            # Count topics across all problems
            all_topics = []
            for topics_str in df[topics_column].dropna():
                topics = [t.strip() for t in str(topics_str).split(',') if t.strip()]
                all_topics.extend(topics)
            
            if all_topics:
                topic_counts = pd.Series(all_topics).value_counts()
                stats['unique_topics'] = len(topic_counts)
                stats['most_common_topics'] = topic_counts.head(20).to_dict()
                stats['total_topic_mentions'] = len(all_topics)
                stats['avg_topics_per_problem'] = len(all_topics) / len(df)
            
            if 'topic_count' in df.columns:
                stats['topic_count_distribution'] = df['topic_count'].value_counts().to_dict()
                stats['avg_topics_per_problem'] = float(df['topic_count'].mean())
                stats['max_topics_per_problem'] = int(df['topic_count'].max())
        
        return stats
    
    def get_topic_cooccurrence_matrix(self, df: pd.DataFrame, topics_column: str = 'topics', 
                                    min_cooccurrence: int = 2) -> pd.DataFrame:
        """Create a co-occurrence matrix for topics (works with non-exploded data).
        
        Args:
            df: DataFrame with non-exploded topics
            topics_column: Name of the topics column
            min_cooccurrence: Minimum co-occurrence count to include in matrix
            
        Returns:
            DataFrame representing topic co-occurrence matrix
        """
        if df.empty or topics_column not in df.columns:
            return pd.DataFrame()
        
        # Get all unique topics
        all_topics = set()
        topic_lists = []
        
        for topics_str in df[topics_column].dropna():
            topics = [t.strip() for t in str(topics_str).split(',') if t.strip()]
            if self.standardize_topics:
                topics = [self._standardize_topic(t) for t in topics]
            topic_lists.append(topics)
            all_topics.update(topics)
        
        all_topics = sorted(list(all_topics))
        
        # Create co-occurrence matrix
        cooccurrence_matrix = pd.DataFrame(0, index=all_topics, columns=all_topics)
        
        for topics in topic_lists:
            for i, topic1 in enumerate(topics):
                for j, topic2 in enumerate(topics):
                    if i != j:  # Don't count self-occurrence
                        cooccurrence_matrix.loc[topic1, topic2] += 1
        
        # Filter by minimum co-occurrence
        mask = cooccurrence_matrix >= min_cooccurrence
        filtered_topics = mask.any(axis=1)
        
        return cooccurrence_matrix.loc[filtered_topics, filtered_topics]