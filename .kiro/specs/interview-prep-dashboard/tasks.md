# Implementation Plan

## LeetCode Metadata Integration Strategy

### Available Metadata (1,922 problems)
The `leetcode_metadata.parquet` file contains rich community and quality data:

**Quality Metrics:**
- `likes` & `dislikes`: Community feedback (avg: 3,424 likes, 460 dislikes)
- `originality_score = likes/(likes+dislikes)`: Problem quality indicator (avg: 0.850)
- `total_votes = likes+dislikes`: Problem age/exposure proxy (range: 6-67,518)
- `acrate`: Acceptance rate indicating difficulty (range: 14.9%-94.5%)

**Content Metadata:**
- `content`: Full problem description for analysis
- `topictags`: Structured topic information
- `ispaidonly`: Premium problem indicator (260 problems)
- `hassolution`: Official solution availability (1,253 problems)
- `hasvideosolution`: Video solution availability (121 problems)

**Key Insights for Analytics:**
1. **Problem Age**: `total_votes` correlates with how long a problem has been available
2. **Problem Quality**: `originality_score` indicates well-formulated, CS-fundamental problems
3. **Hidden Gems**: High originality + low total votes = newer quality problems
4. **Interview Classics**: High likes + high company frequency = essential problems
5. **Difficulty Reality**: `acrate` vs perceived difficulty for better study planning

## Phase 1: Core Shell + Health Monitor + Company Stats

- [x] 1. Backend Verification for Phase 1
  - Test `/api/v1/health/quick` and `/api/v1/health/data` endpoints for reliability
  - Verify `/api/v1/companies/stats` endpoint response shape and timeout behavior
  - Test `/api/v1/companies/{company_name}` for major companies (Google, Amazon, Microsoft)
  - Document actual response times and error patterns for Phase 1 endpoints
  - _Requirements: 6.1, 6.2_

- [x] 2. Project Setup and Foundation
  - Initialize React TypeScript project with Vite build system
  - Configure Material-UI with basic theme (no complex responsive breakpoints)
  - Set up simple state management with React Context (no Redux complexity)
  - Create basic API client with fetch and simple retry logic for 30+ second timeouts
  - _Requirements: 5.1, 6.1_

- [x] 3. Core Shell and Navigation
  - Build basic application layout with header and main content area
  - Create simple navigation with Overview and Company Research tabs
  - Implement basic loading spinner and error message components
  - Add health status indicator in header (green/yellow/red dot)
  - _Requirements: 5.1, 5.2_

- [x] 4. Company Statistics Dashboard
  - Create company list view with basic stats (total problems, difficulty distribution)
  - Build company detail page showing top problems and basic metrics
  - Add simple company search/filter functionality
  - Implement basic error handling when company endpoints fail
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 5. Basic Charts and Visualizations
  - Create simple pie chart for difficulty distribution using Recharts
  - Build basic bar chart for top topics per company
  - Add simple data tables for problem lists with sorting
  - Implement basic localStorage caching for company data
  - _Requirements: 1.1, 1.4_

## Phase 2: Topic Dashboards

- [x] 6. Backend Verification for Phase 2
  - Test `/api/v1/topics/frequency` and `/api/v1/topics/trends` endpoints
  - Verify `/api/v1/topics/heatmap` response format and performance
  - Document which topic endpoints are working vs returning 500 errors
  - Test topic filtering parameters and response consistency
  - _Requirements: 2.1, 2.2_

- [x] 7. Topic Analysis Dashboard
  - Create topic frequency list with simple search functionality
  - Build basic topic trends view showing popular topics
  - Add topic filtering by company (if endpoint supports it)
  - Implement fallback UI when topic endpoints are unavailable
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 8. Topic Visualizations
  - Create simple topic frequency bar chart (TopicFrequencyChart.tsx)
  - Build basic topic heatmap (TopicHeatmapChart.tsx with multiple color schemes, normalization modes)
  - Add topic trend indicators (TopicTrendIndicator.tsx with direction, strength, variants)
  - Implement topic search with basic text matching (TopicAnalysisPage.tsx)
  - _Requirements: 2.1, 2.4_

## Phase 3: Study Planner

- [x] 9. Backend Verification for Phase 3
  - Test `/api/v1/problems/top` and `/api/v1/problems/search` endpoints
  - Verify problem filtering by company and difficulty works reliably
  - Test problem detail endpoint `/api/v1/problems/{problem_title}`
  - Document which problem endpoints provide consistent data for study planning
  - Full API integration with static mode fallback for offline operation
  - _Requirements: 3.1, 3.2_

- [x] 10. Study Plan Generator
  - Create simple form for target companies and study duration
  - Build basic problem recommendation based on company selection
  - Generate simple study schedule with daily problem goals
  - Add basic progress tracking with localStorage persistence
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 11. Study Progress Tracking
  - Create simple progress dashboard showing completed problems
  - Add basic problem marking (completed/skipped/bookmarked)
  - Build simple study streak counter
  - Implement basic study plan export (JSON format)
  - _Requirements: 3.3, 3.4, 7.1_

## Phase 4: Advanced Analytics and Polish

- [x] 12. Backend Verification for Phase 4
  - Test `/api/v1/analytics/correlations` and `/api/v1/analytics/summary` endpoints
  - Verify `/api/v1/analytics/insights` response format and reliability
  - Test company comparison endpoint `/api/v1/companies/compare`
  - Document which advanced analytics endpoints are stable enough for production use
  - _Requirements: 4.1, 4.2_

- [x] 13. Analytics Dashboard
  - Create basic analytics overview with key metrics
  - Build simple correlation analysis (if backend endpoint works)
  - Add basic insights display with actionable recommendations
  - Implement FAANG-specific company comparison (Google, Amazon, Meta, Apple, Netflix)
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 14. LeetCode Metadata Integration
- [x] 14.1 Backend Metadata Processing
  - Load and process leetcode_metadata.parquet into analytics pipeline
  - Calculate derived metrics: originality_score, total_votes, quality_percentiles
  - Create metadata lookup service for problem enrichment
  - Add metadata fields to existing problem endpoints
  - _Requirements: 4.1, 4.3_

- [x] 14.2 Quality Metrics API Endpoints
  - Create `/api/v1/problems/quality-analysis` endpoint
  - Add quality filtering to existing problem search endpoints
  - Implement quality-based problem ranking and sorting
  - Create metadata statistics endpoint for dashboard overview
  - _Requirements: 4.1, 4.3_

- [x] 14.3 Problem Recommendation Engine
  - Build quality-aware recommendation algorithm
  - Implement "Hidden Gems" discovery (high originality, low exposure)
  - Create "Interview Classics" identification (high likes + company frequency)
  - Add quality-based study plan optimization
  - _Requirements: 3.1, 4.3_

- [x] 15. Enhanced Problem Analytics Dashboard
- [x] 15.1 Problem Quality Visualizations
  - Create quality score distribution charts (originality vs. total votes)
  - Build community sentiment heatmaps by topic and difficulty
  - Add acceptance rate vs. perceived difficulty scatter plots
  - Implement quality trend analysis over time
  - _Requirements: 4.3_

- [x] 15.2 Hidden Gems Discovery Interface
  - Build "Hidden Gems" finder with quality filters
  - Create "Rising Stars" section for newer high-quality problems
  - Add "Controversial Problems" analysis with low originality scores
  - Implement quality-based problem recommendations widget
  - _Requirements: 3.1, 4.3_

- [x] 15.3 Enhanced Problem Lists and Filtering
  - Add quality metrics to all problem displays (likes, originality score)
  - Implement advanced filtering by quality, age, and community metrics
  - Create quality-based sorting options for problem lists
  - Add quality indicators and badges to problem cards
  - _Requirements: 1.1, 3.1, 4.3_

- [x] 16. Advanced Study Recommendations
  - Enhance study plan generator with quality metrics (QualityRecommendationsWidget.tsx)
  - Add "balanced learning" mode prioritizing original problems
  - Create "interview classics" mode focusing on most-liked problems
  - Implement adaptive difficulty progression based on acceptance rates
  - Hidden Gems discovery (>85% originality, <2K votes)
  - Rising Stars section (1K-5K votes, >80% quality)
  - Skill-level-aware filtering (beginner/intermediate/advanced)
  - _Requirements: 3.1, 3.2, 4.3_

- [x] 17. Data Export and Sharing
  - Add CSV export for company data and problem lists with quality metrics (exportService.ts)
  - Create simple study plan sharing via JSON export/import
  - Build basic bookmark system for favorite problems with quality scores (BookmarksPage.tsx)
  - Add simple print-friendly views for study materials
  - ExportMenu component with CSV/JSON/Print formats
  - URL-based shareable links for discovery categories
  - _Requirements: 6.3, 7.2_

- [x] 18. Final Polish and Deployment
  - Add basic error boundaries and improved error messages
  - Create simple user onboarding with feature highlights (OnboardingTour.tsx - 5-step guided tour)
  - Build production deployment configuration
  - Add basic environment configuration for API endpoints
  - Responsive design, dark mode support, accessibility features
  - _Requirements: 5.4, 6.4_

## Phase 5: Advanced Metadata Analytics (Future Enhancements)

- [x] 22. Personalized Learning Paths
  - Quality-aware study plan generation based on user skill level
  - Adaptive difficulty progression using acceptance rates and quality scores
  - "Balanced Portfolio" approach: mix of classics, gems, and trending problems
  - Learning efficiency optimization using community feedback data

## Backlog (Advanced Features - Not MVP)

### Technical Enhancements
- IndexedDB caching system for metadata
- Service worker and offline functionality
- Advanced correlation matrices including quality metrics
- Venn diagrams for company overlap analysis with quality weighting
- Predictive modeling for problem success rates
- Real-time insights generation from community data
- Advanced data visualization (network graphs, quality heatmaps)
- Mobile-specific optimizations and PWA features

### Analytics & Intelligence
- Machine learning models for problem recommendation
- Sentiment analysis of problem content and community feedback
- Predictive analytics for interview success based on study patterns
- Advanced statistical analysis of problem characteristics
- Time-series analysis of problem popularity and difficulty trends
- Cross-platform analytics integration (LeetCode, HackerRank, etc.)

### User Experience
- Comprehensive testing suite
- Performance optimizations (virtual scrolling, code splitting)
- Advanced export formats (PDF reports, calendar integration)
- User authentication and cloud sync
- Social features (study groups, progress sharing)
- Gamification elements based on problem quality achievements