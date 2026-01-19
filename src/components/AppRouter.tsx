import React from 'react';
import { useAppContext } from '../hooks/useAppContext';
import { OverviewPage } from '../pages/OverviewPage';
import { CompanyResearchPage } from '../pages/CompanyResearchPage';
import { TopicAnalysisPage } from '../pages/TopicAnalysisPage';
import { StudyPlannerPage } from '../pages/StudyPlannerPage';
import { AnalyticsPage } from '../pages/AnalyticsPage';
import BookmarksPage from '../pages/BookmarksPage';
import { LoadingSpinner } from './Common';

export function AppRouter() {
  const { state } = useAppContext();

  // Simple routing based on current view state
  const renderCurrentPage = () => {
    switch (state.currentView) {
      case 'overview':
        return <OverviewPage />;
      case 'company':
        return <CompanyResearchPage />;
      case 'topics':
        return <TopicAnalysisPage />;
      case 'study':
        return <StudyPlannerPage />;
      case 'analytics':
        return <AnalyticsPage />;
      case 'bookmarks':
        return <BookmarksPage />;
      default:
        return <OverviewPage />;
    }
  };

  return (
    <React.Suspense fallback={<LoadingSpinner message="Loading page..." />}>
      {renderCurrentPage()}
    </React.Suspense>
  );
}
