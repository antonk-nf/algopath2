// Export service for data export and sharing functionality
import type { CompanyData, ProblemData, StudyPlan } from '../types';

export interface ExportOptions {
  format?: 'csv' | 'json';
  includeQualityMetrics?: boolean;
  includeHeaders?: boolean;
  filename?: string;
}

export interface BookmarkedProblem extends ProblemData {
  bookmarkedAt: string;
  notes?: string;
  tags?: string[];
  priority?: 'high' | 'medium' | 'low';
}

export class ExportService {
  // CSV Export functionality
  static exportCompanyDataToCSV(companies: CompanyData[], options: ExportOptions = {}): void {
    const headers = [
      'Company',
      'Total Problems',
      'Unique Problems',
      'Average Frequency',
      'Average Acceptance Rate',
      'Easy Problems',
      'Medium Problems',
      'Hard Problems',
      'Unknown Difficulty',
      'Top Topics',
      'Timeframe Coverage',
      'Rank'
    ];

    const rows = companies.map(company => [
      company.company,
      company.totalProblems.toString(),
      company.uniqueProblems.toString(),
      company.avgFrequency.toFixed(2),
      (company.avgAcceptanceRate * 100).toFixed(1) + '%',
      company.difficultyDistribution.EASY.toString(),
      company.difficultyDistribution.MEDIUM.toString(),
      company.difficultyDistribution.HARD.toString(),
      company.difficultyDistribution.UNKNOWN.toString(),
      company.topTopics.join('; '),
      company.timeframeCoverage.join('; '),
      company.rank?.toString() || 'N/A'
    ]);

    const csvContent = this.arrayToCSV([headers, ...rows]);
    const filename = options.filename || `company-data-${this.getDateString()}.csv`;
    this.downloadFile(csvContent, filename, 'text/csv');
  }

  static exportProblemsToCSV(problems: ProblemData[], options: ExportOptions = {}): void {
    const baseHeaders = [
      'Title',
      'Difficulty',
      'Company Count',
      'Acceptance Rate',
      'Topics',
      'Company',
      'Timeframe',
      'Total Frequency',
      'Company Count',
      'Link'
    ];

    const qualityHeaders = options.includeQualityMetrics ? [
      'Likes',
      'Dislikes',
      'Originality Score',
      'Total Votes',
      'Quality Tier',
      'Has Official Solution',
      'Has Video Solution',
      'Is Paid Only'
    ] : [];

    const headers = [...baseHeaders, ...qualityHeaders];

    const rows = problems.map(problem => {
      const baseRow = [
        problem.title,
        problem.difficulty,
        problem.companyCount?.toString() || 'N/A',
        problem.acceptanceRate ? (problem.acceptanceRate * 100).toFixed(1) + '%' : 'N/A',
        problem.topics.join('; '),
        problem.company,
        problem.timeframe || 'N/A',
        problem.totalFrequency?.toString() || 'N/A',
        problem.companyCount?.toString() || 'N/A',
        problem.link || 'N/A'
      ];

      const qualityRow = options.includeQualityMetrics ? [
        problem.likes?.toString() || 'N/A',
        problem.dislikes?.toString() || 'N/A',
        problem.originalityScore?.toFixed(3) || 'N/A',
        problem.totalVotes?.toString() || 'N/A',
        problem.qualityTier || 'N/A',
        problem.hasOfficialSolution?.toString() || 'N/A',
        problem.hasVideoSolution?.toString() || 'N/A',
        problem.isPaidOnly?.toString() || 'N/A'
      ] : [];

      return [...baseRow, ...qualityRow];
    });

    const csvContent = this.arrayToCSV([headers, ...rows]);
    const filename = options.filename || `problems-data-${this.getDateString()}.csv`;
    this.downloadFile(csvContent, filename, 'text/csv');
  }

  // Study Plan Export/Import
  static exportStudyPlan(studyPlan: StudyPlan): void {
    const exportData = {
      ...studyPlan,
      exportedAt: new Date().toISOString(),
      version: '1.0'
    };

    const jsonContent = JSON.stringify(exportData, null, 2);
    const filename = `study-plan-${studyPlan.name.replace(/\s+/g, '-')}-${this.getDateString()}.json`;
    this.downloadFile(jsonContent, filename, 'application/json');
  }

  static exportMultipleStudyPlans(studyPlans: StudyPlan[]): void {
    const exportData = {
      studyPlans,
      exportedAt: new Date().toISOString(),
      version: '1.0',
      count: studyPlans.length
    };

    const jsonContent = JSON.stringify(exportData, null, 2);
    const filename = `study-plans-backup-${this.getDateString()}.json`;
    this.downloadFile(jsonContent, filename, 'application/json');
  }

  /**
   * Export study plan to ICS calendar format
   * Creates calendar events for each problem in the study plan
   */
  static exportStudyPlanToICS(studyPlan: StudyPlan): void {
    const formatICSDate = (date: Date): string => {
      return date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
    };

    const escapeICSText = (text: string): string => {
      return text
        .replace(/\\/g, '\\\\')
        .replace(/,/g, '\\,')
        .replace(/;/g, '\\;')
        .replace(/\n/g, '\\n');
    };

    let ics = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//LeetCode Interview Prep//EN',
      'CALSCALE:GREGORIAN',
      'METHOD:PUBLISH',
      `X-WR-CALNAME:${escapeICSText(studyPlan.name)}`,
    ].join('\r\n') + '\r\n';

    studyPlan.schedule.forEach((session, dayIndex) => {
      session.problems.forEach((problem, problemIndex) => {
        // Parse session date and set start time (9 AM)
        const sessionDate = new Date(session.date);
        sessionDate.setHours(9 + problemIndex, 0, 0, 0); // Stagger problems by 1 hour

        // End time is 1 hour after start
        const endDate = new Date(sessionDate);
        endDate.setHours(endDate.getHours() + 1);

        const uid = `${studyPlan.id}-day${dayIndex}-p${problemIndex}@leetcode-prep`;
        const summary = `LeetCode: ${problem.title} (${problem.difficulty})`;
        const description = [
          `Topics: ${problem.topics.join(', ')}`,
          `Company: ${problem.company}`,
          problem.link ? `Link: ${problem.link}` : '',
          `Status: ${problem.status}`,
        ].filter(Boolean).join('\\n');

        ics += [
          'BEGIN:VEVENT',
          `UID:${uid}`,
          `DTSTAMP:${formatICSDate(new Date())}`,
          `DTSTART:${formatICSDate(sessionDate)}`,
          `DTEND:${formatICSDate(endDate)}`,
          `SUMMARY:${escapeICSText(summary)}`,
          `DESCRIPTION:${escapeICSText(description)}`,
          problem.link ? `URL:${problem.link}` : '',
          `CATEGORIES:LeetCode,${problem.difficulty}`,
          'STATUS:CONFIRMED',
          'END:VEVENT',
        ].filter(Boolean).join('\r\n') + '\r\n';
      });
    });

    ics += 'END:VCALENDAR\r\n';

    const filename = `study-plan-${studyPlan.name.replace(/\s+/g, '-').toLowerCase()}-${this.getDateString()}.ics`;
    this.downloadFile(ics, filename, 'text/calendar');
  }

  static async importStudyPlans(file: File): Promise<StudyPlan[]> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const content = e.target?.result as string;
          const data = JSON.parse(content);
          
          // Handle both single plan and multiple plans format
          if (data.studyPlans && Array.isArray(data.studyPlans)) {
            resolve(data.studyPlans);
          } else if (data.id && data.name) {
            // Single study plan
            resolve([data]);
          } else {
            reject(new Error('Invalid study plan file format'));
          }
        } catch (error) {
          reject(new Error('Failed to parse study plan file'));
        }
      };
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsText(file);
    });
  }

  // Bookmark functionality
  static getBookmarkedProblems(): BookmarkedProblem[] {
    const bookmarks = localStorage.getItem('bookmarked-problems');
    return bookmarks ? JSON.parse(bookmarks) : [];
  }

  static addBookmark(problem: ProblemData, notes?: string, tags?: string[], priority?: 'high' | 'medium' | 'low'): void {
    const bookmarks = this.getBookmarkedProblems();
    const existingIndex = bookmarks.findIndex(b => b.title === problem.title);
    
    const bookmark: BookmarkedProblem = {
      ...problem,
      bookmarkedAt: new Date().toISOString(),
      notes,
      tags: tags || [],
      priority: priority || 'medium'
    };

    if (existingIndex >= 0) {
      bookmarks[existingIndex] = bookmark;
    } else {
      bookmarks.push(bookmark);
    }

    localStorage.setItem('bookmarked-problems', JSON.stringify(bookmarks));
  }

  static removeBookmark(problemTitle: string): void {
    const bookmarks = this.getBookmarkedProblems();
    const filtered = bookmarks.filter(b => b.title !== problemTitle);
    localStorage.setItem('bookmarked-problems', JSON.stringify(filtered));
  }

  static isBookmarked(problemTitle: string): boolean {
    const bookmarks = this.getBookmarkedProblems();
    return bookmarks.some(b => b.title === problemTitle);
  }

  static exportBookmarks(): void {
    const bookmarks = this.getBookmarkedProblems();
    const exportData = {
      bookmarks,
      exportedAt: new Date().toISOString(),
      version: '1.0',
      count: bookmarks.length
    };

    const jsonContent = JSON.stringify(exportData, null, 2);
    const filename = `bookmarked-problems-${this.getDateString()}.json`;
    this.downloadFile(jsonContent, filename, 'application/json');
  }

  static exportBookmarksToCSV(): void {
    const bookmarks = this.getBookmarkedProblems();
    
    const headers = [
      'Title',
      'Difficulty',
      'Topics',
      'Company',
      'Bookmarked At',
      'Priority',
      'Tags',
      'Notes',
      'Likes',
      'Dislikes',
      'Originality Score',
      'Quality Tier',
      'Link'
    ];

    const rows = bookmarks.map(bookmark => [
      bookmark.title,
      bookmark.difficulty,
      bookmark.topics.join('; '),
      bookmark.company,
      new Date(bookmark.bookmarkedAt).toLocaleDateString(),
      bookmark.priority || 'medium',
      bookmark.tags?.join('; ') || '',
      bookmark.notes || '',
      bookmark.likes?.toString() || 'N/A',
      bookmark.dislikes?.toString() || 'N/A',
      bookmark.originalityScore?.toFixed(3) || 'N/A',
      bookmark.qualityTier || 'N/A',
      bookmark.link || 'N/A'
    ]);

    const csvContent = this.arrayToCSV([headers, ...rows]);
    const filename = `bookmarked-problems-${this.getDateString()}.csv`;
    this.downloadFile(csvContent, filename, 'text/csv');
  }

  // Print-friendly data formatting
  static generatePrintableStudyMaterial(studyPlan: StudyPlan): string {
    const problems = studyPlan.schedule.flatMap(session => session.problems);
    
    let content = `
# Study Plan: ${studyPlan.name}

**Target Companies:** ${studyPlan.targetCompanies.join(', ')}
**Duration:** ${studyPlan.duration} weeks
**Daily Goal:** ${studyPlan.dailyGoal} problems per day
**Focus Areas:** ${studyPlan.focusAreas.join(', ')}
**Created:** ${new Date(studyPlan.createdAt).toLocaleDateString()}

## Progress Summary
- **Total Problems:** ${studyPlan.progress.totalProblems}
- **Completed:** ${studyPlan.progress.completedProblems}
- **Completion Rate:** ${studyPlan.progress.completionRate.toFixed(1)}%
- **Current Streak:** ${studyPlan.progress.currentStreak} days

## Problems by Difficulty
- **Easy:** ${studyPlan.progress.difficultyBreakdown.EASY.completed}/${studyPlan.progress.difficultyBreakdown.EASY.total}
- **Medium:** ${studyPlan.progress.difficultyBreakdown.MEDIUM.completed}/${studyPlan.progress.difficultyBreakdown.MEDIUM.total}
- **Hard:** ${studyPlan.progress.difficultyBreakdown.HARD.completed}/${studyPlan.progress.difficultyBreakdown.HARD.total}

## Problem List

`;

    problems.forEach((problem, index) => {
      const status = problem.status === 'completed' ? '✅' : 
                   problem.status === 'skipped' ? '⏭️' : 
                   problem.status === 'in_progress' ? '🔄' : '⭕';
      
      content += `${index + 1}. ${status} **${problem.title}** (${problem.difficulty})
   - Topics: ${problem.topics.join(', ')}
   - Company: ${problem.company}`;
      
      if (problem.qualityScore) {
        content += `
   - Quality Score: ${problem.qualityScore.toFixed(2)}`;
      }
      
      if (problem.notes) {
        content += `
   - Notes: ${problem.notes}`;
      }
      
      content += '\n\n';
    });

    return content;
  }

  // Utility methods
  private static arrayToCSV(data: string[][]): string {
    return data.map(row => 
      row.map(field => {
        // Escape quotes and wrap in quotes if contains comma, quote, or newline
        if (field.includes(',') || field.includes('"') || field.includes('\n')) {
          return `"${field.replace(/"/g, '""')}"`;
        }
        return field;
      }).join(',')
    ).join('\n');
  }

  private static downloadFile(content: string, filename: string, mimeType: string): void {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  private static getDateString(): string {
    return new Date().toISOString().split('T')[0];
  }
}
