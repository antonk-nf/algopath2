"""Advanced analytics API endpoints."""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
import pandas as pd

from ..dependencies import (
    get_analytics_engine,
    get_unified_dataset,
    get_correlation_id,
    get_dataset_validator
)
from ..models import (
    CorrelationResponse,
    TimeframeFilter,
    DifficultyFilter
)
from ..exceptions import ValidationError, DataProcessingError
from ...analytics.analytics_engine import AnalyticsEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/correlations", response_model=Dict[str, Any])
async def get_correlations(
    # Query parameters
    metric: str = Query("composite", description="Metric to analyze correlations for"),
    companies: Optional[List[str]] = Query(None, description="Filter by companies"),
    min_correlation: Optional[float] = Query(0.1, ge=-1, le=1, description="Minimum correlation strength"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of correlations"),
    
    # Dependencies
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine),
    dataset = Depends(get_unified_dataset),
    dataset_validator = Depends(get_dataset_validator),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get cross-metric correlation analysis.
    
    Analyzes correlations between companies, problems, or topics based on
    the specified metric (frequency, difficulty, topics).
    """
    try:
        logger.info(f"Analyzing correlations for metric: {metric}", extra={"correlation_id": correlation_id})
        
        # Validate metric
        valid_metrics = ["frequency", "difficulty", "topics", "acceptance_rate", "composite"]
        if metric not in valid_metrics:
            raise ValidationError(f"Invalid metric '{metric}'. Valid options: {', '.join(valid_metrics)}")
        
        # Validate companies against dataset
        companies = dataset_validator.validate_companies(companies)
        
        # Get correlations from analytics engine
        correlations_result = analytics_engine.get_company_correlations(
            dataset,
            metric,
            companies_filter=companies
        )
        
        if not correlations_result:
            logger.warning(f"No correlations found for metric: {metric}", extra={"correlation_id": correlation_id})
            return {
                "correlations": [],
                "correlation_matrix": {},
                "metadata": {
                    "metric": metric,
                    "total_correlations": 0,
                    "min_correlation_threshold": min_correlation,
                    "analysis_type": f"{metric}_correlation"
                }
            }
        
        # Filter correlations by minimum threshold
        correlations = correlations_result.get('top_correlations', [])
        if min_correlation is not None:
            correlations = [
                corr for corr in correlations 
                if abs(corr.get('correlation', 0)) >= min_correlation
            ]
        
        # Limit results
        correlations = correlations[:limit]
        
        analyzed_companies = correlations_result.get('companies_analyzed')
        if not analyzed_companies:
            analyzed_companies = companies if companies else sorted(dataset['company'].unique().tolist())

        result = {
            "correlations": correlations,
            "correlation_matrix": correlations_result.get('correlation_matrix', {}),
            "metadata": {
                "metric": metric,
                "total_correlations": len(correlations),
                "min_correlation_threshold": min_correlation,
                "analysis_type": correlations_result.get('analysis_type', f"{metric}_correlation"),
                "companies_analyzed": analyzed_companies,
                "total_companies": len(analyzed_companies)
            }
        }
        
        logger.info(
            f"Returning {len(correlations)} correlations for metric: {metric}",
            extra={"correlation_id": correlation_id}
        )
        
        return result
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error analyzing correlations: {str(e)}", extra={"correlation_id": correlation_id})
        raise DataProcessingError(f"Failed to analyze correlations: {str(e)}")


@router.get("/difficulty", response_model=Dict[str, Any])
async def get_difficulty_analysis(
    # Query parameters
    groupby: str = Query("overall", description="How to group the analysis"),
    companies: Optional[List[str]] = Query(None, description="Filter by companies"),
    timeframes: Optional[List[TimeframeFilter]] = Query(None, description="Filter by timeframes"),
    
    # Dependencies
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine),
    dataset = Depends(get_unified_dataset),
    dataset_validator = Depends(get_dataset_validator),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get comprehensive difficulty analysis.
    
    Analyzes difficulty distributions, acceptance rate correlations,
    and difficulty preferences across companies and topics.
    """
    try:
        logger.info(f"Analyzing difficulty with groupby: {groupby}", extra={"correlation_id": correlation_id})
        
        # Validate groupby parameter
        valid_groupby = ["overall", "company", "timeframe", "topics"]
        if groupby not in valid_groupby:
            raise ValidationError(f"Invalid groupby '{groupby}'. Valid options: {', '.join(valid_groupby)}")
        
        # Validate companies against dataset
        companies = dataset_validator.validate_companies(companies)
        
        # Filter dataset if needed
        filtered_dataset = dataset.copy()
        if companies:
            filtered_dataset = filtered_dataset[filtered_dataset['company'].isin(companies)]
        
        if timeframes:
            timeframe_values = [tf.value for tf in timeframes]
            filtered_dataset = filtered_dataset[filtered_dataset['timeframe'].isin(timeframe_values)]
        
        # Get difficulty analysis from analytics engine
        difficulty_stats = analytics_engine.calculate_difficulty_stats(filtered_dataset, groupby)
        
        if difficulty_stats.empty:
            logger.warning("No difficulty analysis data found", extra={"correlation_id": correlation_id})
            return {
                "difficulty_distribution": {},
                "acceptance_rate_analysis": {},
                "outliers": [],
                "metadata": {
                    "groupby": groupby,
                    "total_records": 0,
                    "companies_analyzed": 0
                }
            }
        
        # Additional analyses
        result = {
            "difficulty_distribution": difficulty_stats.to_dict('records') if not difficulty_stats.empty else [],
            "metadata": {
                "groupby": groupby,
                "total_records": len(filtered_dataset),
                "companies_analyzed": len(companies) if companies else len(filtered_dataset['company'].unique()),
                "timeframes_analyzed": len(timeframes) if timeframes else len(filtered_dataset['timeframe'].unique())
            }
        }
        
        # Add acceptance rate analysis
        acceptance_analysis = analytics_engine.difficulty_analyzer.analyze_acceptance_rate_by_difficulty(filtered_dataset)
        result["acceptance_rate_analysis"] = acceptance_analysis.to_dict('records') if not acceptance_analysis.empty else []
        
        # Add outlier detection
        outliers = analytics_engine.difficulty_analyzer.detect_acceptance_rate_outliers(filtered_dataset)
        result["outliers"] = outliers.to_dict('records') if not outliers.empty else []
        
        # Add company difficulty preferences if not already grouped by company
        if groupby != "company":
            preferences = analytics_engine.difficulty_analyzer.analyze_company_difficulty_preferences(filtered_dataset)
            result["company_preferences"] = preferences.to_dict('records') if not preferences.empty else []
        
        logger.info(
            f"Returning difficulty analysis with {len(result['difficulty_distribution'])} records",
            extra={"correlation_id": correlation_id}
        )
        
        return result
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error analyzing difficulty: {str(e)}", extra={"correlation_id": correlation_id})
        raise DataProcessingError(f"Failed to analyze difficulty: {str(e)}")


@router.get("/trends", response_model=Dict[str, Any])
async def get_trend_analysis(
    # Query parameters
    analysis_type: str = Query("problems", description="Type of trend analysis"),
    companies: Optional[List[str]] = Query(None, description="Filter by companies"),
    timeframes: Optional[List[TimeframeFilter]] = Query(None, description="Filter by timeframes"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    
    # Dependencies
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine),
    dataset = Depends(get_unified_dataset),
    dataset_validator = Depends(get_dataset_validator),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get comprehensive trend analysis.
    
    Analyzes trends in problems, companies, or topics over different timeframes
    with momentum change detection and emerging pattern identification.
    """
    try:
        logger.info(f"Analyzing trends for: {analysis_type}", extra={"correlation_id": correlation_id})
        
        # Validate analysis type
        valid_types = ["problems", "companies", "topics", "momentum"]
        if analysis_type not in valid_types:
            raise ValidationError(f"Invalid analysis_type '{analysis_type}'. Valid options: {', '.join(valid_types)}")
        
        # Validate companies against dataset
        companies = dataset_validator.validate_companies(companies)
        
        # Filter dataset if needed
        filtered_dataset = dataset.copy()
        if companies:
            filtered_dataset = filtered_dataset[filtered_dataset['company'].isin(companies)]
        
        if timeframes:
            timeframe_values = [tf.value for tf in timeframes]
            filtered_dataset = filtered_dataset[filtered_dataset['timeframe'].isin(timeframe_values)]
        
        # Get trend analysis based on type
        result = {}
        
        if analysis_type == "problems":
            trends_df = analytics_engine.trend_analyzer.analyze_problem_trends(filtered_dataset)
            result["problem_trends"] = trends_df.head(limit).to_dict('records') if not trends_df.empty else []
            
        elif analysis_type == "companies":
            trends_df = analytics_engine.trend_analyzer.analyze_company_trends(filtered_dataset)
            result["company_trends"] = trends_df.head(limit).to_dict('records') if not trends_df.empty else []
            
        elif analysis_type == "topics":
            trends_df = analytics_engine.topic_analyzer.analyze_topic_trends(filtered_dataset)
            result["topic_trends"] = trends_df.head(limit).to_dict('records') if not trends_df.empty else []
            
        elif analysis_type == "momentum":
            momentum_df = analytics_engine.trend_analyzer.identify_momentum_changes(filtered_dataset)
            result["momentum_changes"] = momentum_df.head(limit).to_dict('records') if not momentum_df.empty else []
        
        # Add metadata
        result["metadata"] = {
            "analysis_type": analysis_type,
            "total_records": len(filtered_dataset),
            "companies_analyzed": len(companies) if companies else len(filtered_dataset['company'].unique()),
            "timeframes_analyzed": len(timeframes) if timeframes else len(filtered_dataset['timeframe'].unique()),
            "results_returned": len(result.get(f"{analysis_type}_trends", result.get("momentum_changes", [])))
        }
        
        logger.info(
            f"Returning {analysis_type} trend analysis with {result['metadata']['results_returned']} results",
            extra={"correlation_id": correlation_id}
        )
        
        return result
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error analyzing trends: {str(e)}", extra={"correlation_id": correlation_id})
        raise DataProcessingError(f"Failed to analyze trends: {str(e)}")


@router.get("/summary", response_model=Dict[str, Any])
async def get_analytics_summary(
    # Query parameters
    companies: Optional[List[str]] = Query(None, description="Filter by companies"),
    timeframes: Optional[List[TimeframeFilter]] = Query(None, description="Filter by timeframes"),
    
    # Dependencies
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine),
    dataset = Depends(get_unified_dataset),
    dataset_validator = Depends(get_dataset_validator),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get comprehensive analytics summary.
    
    Returns a high-level overview of all analytics capabilities and
    key insights from the dataset.
    """
    try:
        logger.info("Generating comprehensive analytics summary", extra={"correlation_id": correlation_id})
        
        # Validate companies against dataset
        companies = dataset_validator.validate_companies(companies)
        
        # Filter dataset if needed
        filtered_dataset = dataset.copy()
        if companies:
            filtered_dataset = filtered_dataset[filtered_dataset['company'].isin(companies)]
        
        if timeframes:
            timeframe_values = [tf.value for tf in timeframes]
            filtered_dataset = filtered_dataset[filtered_dataset['timeframe'].isin(timeframe_values)]
        
        # Get comprehensive analytics summary
        summary = analytics_engine.get_analytics_summary(filtered_dataset)
        
        # Add filter information
        summary["filters_applied"] = {
            "companies": companies,
            "timeframes": [tf.value for tf in timeframes] if timeframes else None,
            "total_companies_in_result": len(filtered_dataset['company'].unique()),
            "total_problems_in_result": len(filtered_dataset)
        }
        
        logger.info(
            f"Generated comprehensive analytics summary for {len(filtered_dataset)} records",
            extra={"correlation_id": correlation_id}
        )
        
        return summary
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error generating analytics summary: {str(e)}", extra={"correlation_id": correlation_id})
        raise DataProcessingError(f"Failed to generate analytics summary: {str(e)}")


@router.get("/insights", response_model=Dict[str, Any])
async def get_key_insights(
    # Query parameters
    companies: Optional[List[str]] = Query(None, description="Filter by companies"),
    timeframes: Optional[List[TimeframeFilter]] = Query(None, description="Filter by timeframes"),
    
    # Dependencies
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine),
    dataset = Depends(get_unified_dataset),
    dataset_validator = Depends(get_dataset_validator),
    correlation_id: str = Depends(get_correlation_id)
):
    """
    Get key insights and recommendations.
    
    Returns actionable insights derived from the data analysis,
    including trending topics, emerging patterns, and recommendations.
    """
    try:
        logger.info("Generating key insights", extra={"correlation_id": correlation_id})
        
        # Validate companies against dataset
        companies = dataset_validator.validate_companies(companies)
        
        # Filter dataset if needed
        filtered_dataset = dataset.copy()
        if companies:
            filtered_dataset = filtered_dataset[filtered_dataset['company'].isin(companies)]
        
        if timeframes:
            timeframe_values = [tf.value for tf in timeframes]
            filtered_dataset = filtered_dataset[filtered_dataset['timeframe'].isin(timeframe_values)]
        
        # Generate insights
        insights = {
            "key_findings": [],
            "trending_topics": [],
            "emerging_patterns": [],
            "recommendations": [],
            "metadata": {
                "analysis_date": pd.Timestamp.now().isoformat(),
                "data_coverage": {
                    "companies": len(filtered_dataset['company'].unique()),
                    "problems": len(filtered_dataset),
                    "unique_problems": filtered_dataset['title'].nunique(),
                    "timeframes": sorted(filtered_dataset['timeframe'].unique().tolist())
                }
            }
        }
        
        # Top problems insight
        top_problems = analytics_engine.get_top_problems(filtered_dataset, limit=5)
        if not top_problems.empty:
            insights["key_findings"].append({
                "type": "top_problems",
                "title": "Most Frequently Asked Problems",
                "description": f"The top 5 most frequently asked problems across {len(filtered_dataset['company'].unique())} companies",
                "data": top_problems[['title', 'total_frequency', 'company_count']].to_dict('records')
            })
        
        # Trending topics
        topic_trends = analytics_engine.topic_analyzer.analyze_topic_trends(filtered_dataset)
        if not topic_trends.empty:
            trending = topic_trends.head(10)
            insights["trending_topics"] = trending.to_dict('records')
            
            insights["key_findings"].append({
                "type": "trending_topics",
                "title": "Trending Technical Topics",
                "description": f"Top {len(trending)} trending topics based on frequency changes",
                "data": trending[['topic', 'trend_direction']].to_dict('records') if 'topic' in trending.columns else []
            })
        
        # Difficulty distribution insight
        difficulty_dist = filtered_dataset['difficulty'].value_counts(normalize=True)
        insights["key_findings"].append({
            "type": "difficulty_distribution",
            "title": "Problem Difficulty Distribution",
            "description": "Distribution of problems by difficulty level",
            "data": {
                "percentages": difficulty_dist.to_dict(),
                "most_common": difficulty_dist.index[0] if not difficulty_dist.empty else None
            }
        })
        
        # Company diversity insight
        company_problem_counts = filtered_dataset.groupby('company')['title'].nunique().sort_values(ascending=False)
        insights["key_findings"].append({
            "type": "company_diversity",
            "title": "Company Problem Diversity",
            "description": "Companies with the most diverse problem sets",
            "data": {
                "top_companies": company_problem_counts.head(5).to_dict(),
                "average_problems_per_company": float(company_problem_counts.mean())
            }
        })
        
        # Generate recommendations
        recommendations = []
        
        if not top_problems.empty:
            top_problem = top_problems.iloc[0]
            recommendations.append({
                "type": "study_priority",
                "title": "High Priority Problem",
                "description": f"Focus on '{top_problem['title']}' - asked by {top_problem['company_count']} companies",
                "action": "prioritize_study",
                "confidence": "high"
            })
        
        if 'MEDIUM' in difficulty_dist and difficulty_dist['MEDIUM'] > 0.5:
            recommendations.append({
                "type": "difficulty_focus",
                "title": "Medium Difficulty Focus",
                "description": "Medium difficulty problems dominate the dataset - focus preparation here",
                "action": "focus_medium_problems",
                "confidence": "medium"
            })
        
        insights["recommendations"] = recommendations
        
        logger.info(
            f"Generated {len(insights['key_findings'])} key insights and {len(recommendations)} recommendations",
            extra={"correlation_id": correlation_id}
        )
        
        return insights
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}", extra={"correlation_id": correlation_id})
        raise DataProcessingError(f"Failed to generate insights: {str(e)}")
