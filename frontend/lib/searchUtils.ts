import { Job } from './types';

// Text preprocessing utilities
export class TextProcessor {
  static preprocess(text: string): string {
    return text
      .toLowerCase()
      .replace(/[^\w\s]/g, ' ') // Remove punctuation
      .replace(/\s+/g, ' ') // Normalize whitespace
      .trim();
  }

  static tokenize(text: string): string[] {
    return this.preprocess(text).split(' ').filter(word => word.length > 2);
  }

  static removeStopWords(tokens: string[]): string[] {
    const stopWords = new Set([
      'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
      'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after',
      'above', 'below', 'between', 'among', 'is', 'are', 'was', 'were', 'be',
      'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
      'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
      'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
      'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'a', 'an'
    ]);
    
    return tokens.filter(token => !stopWords.has(token));
  }

  static stemWord(word: string): string {
    // Simple stemming - remove common suffixes
    const suffixes = ['ing', 'ed', 'er', 'est', 'ly', 'tion', 'sion', 'ness', 'ment'];
    
    for (const suffix of suffixes) {
      if (word.endsWith(suffix) && word.length > suffix.length + 2) {
        return word.slice(0, -suffix.length);
      }
    }
    
    return word;
  }

  static processText(text: string): string[] {
    const tokens = this.tokenize(text);
    const withoutStopWords = this.removeStopWords(tokens);
    return withoutStopWords.map(token => this.stemWord(token));
  }
}

// TF-IDF implementation
export class TFIDF {
  private documentFrequencies: Map<string, number> = new Map();
  private totalDocuments: number = 0;

  constructor(jobs: Job[]) {
    this.totalDocuments = jobs.length;
    this.calculateDocumentFrequencies(jobs);
  }

  private calculateDocumentFrequencies(jobs: Job[]): void {
    const docFreq = new Map<string, Set<number>>();

    jobs.forEach((job, index) => {
      const text = this.getJobText(job);
      const terms = TextProcessor.processText(text);
      
      terms.forEach(term => {
        if (!docFreq.has(term)) {
          docFreq.set(term, new Set());
        }
        docFreq.get(term)!.add(index);
      });
    });

    // Convert to document frequencies
    docFreq.forEach((docSet, term) => {
      this.documentFrequencies.set(term, docSet.size);
    });
  }

  private getJobText(job: Job): string {
    return [
      job.title,
      job.company,
      job.description || '',
      job.ai_generated_summary || '',
      job.skills_required?.join(' ') || '',
      job.location || ''
    ].join(' ');
  }

  private calculateTF(terms: string[], term: string): number {
    const count = terms.filter(t => t === term).length;
    return count / terms.length;
  }

  private calculateIDF(term: string): number {
    const docFreq = this.documentFrequencies.get(term) || 0;
    if (docFreq === 0) return 0;
    return Math.log(this.totalDocuments / docFreq);
  }

  getTFIDFVector(terms: string[]): Map<string, number> {
    const vector = new Map<string, number>();
    const uniqueTerms = Array.from(new Set(terms));

    uniqueTerms.forEach(term => {
      const tf = this.calculateTF(terms, term);
      const idf = this.calculateIDF(term);
      vector.set(term, tf * idf);
    });

    return vector;
  }
}

// Cosine similarity calculation
export class CosineSimilarity {
  static calculate(vectorA: Map<string, number>, vectorB: Map<string, number>): number {
    const allTerms = new Set(Array.from(vectorA.keys()).concat(Array.from(vectorB.keys())));
    
    let dotProduct = 0;
    let normA = 0;
    let normB = 0;

    allTerms.forEach(term => {
      const a = vectorA.get(term) || 0;
      const b = vectorB.get(term) || 0;
      
      dotProduct += a * b;
      normA += a * a;
      normB += b * b;
    });

    if (normA === 0 || normB === 0) return 0;
    
    return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
  }
}

// Advanced search algorithm
export class IntelligentSearch {
  private tfidf: TFIDF;
  private jobs: Job[];

  constructor(jobs: Job[]) {
    this.jobs = jobs;
    this.tfidf = new TFIDF(jobs);
  }

  search(query: string, limit: number = 50): Job[] {
    if (!query.trim()) return this.jobs;

    const queryTerms = TextProcessor.processText(query);
    const queryVector = this.tfidf.getTFIDFVector(queryTerms);

    // Calculate similarity scores for each job
    const scoredJobs = this.jobs.map(job => {
      const jobText = this.getJobText(job);
      const jobTerms = TextProcessor.processText(jobText);
      const jobVector = this.tfidf.getTFIDFVector(jobTerms);
      
      const cosineSimilarity = CosineSimilarity.calculate(queryVector, jobVector);
      
      // Boost scores for exact matches in important fields
      const exactMatchBoost = this.calculateExactMatchBoost(job, query);
      
      // Boost scores for skill matches
      const skillMatchBoost = this.calculateSkillMatchBoost(job, queryTerms);
      
      // Boost scores for recent jobs
      const recencyBoost = this.calculateRecencyBoost(job);
      
      // Boost scores for remote work
      const remoteWorkBoost = this.calculateRemoteWorkBoost(job);
      
      const finalScore = cosineSimilarity + exactMatchBoost + skillMatchBoost + recencyBoost + remoteWorkBoost;

      return { job, score: finalScore };
    });

    // Sort by score and return top results
    return scoredJobs
      .filter(item => item.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, limit)
      .map(item => item.job);
  }

  private getJobText(job: Job): string {
    return [
      job.title,
      job.company,
      job.description || '',
      job.ai_generated_summary || '',
      job.skills_required?.join(' ') || '',
      job.location || ''
    ].join(' ');
  }

  private calculateExactMatchBoost(job: Job, query: string): number {
    const queryLower = query.toLowerCase();
    let boost = 0;

    // Title exact match (highest boost)
    if (job.title.toLowerCase().includes(queryLower)) {
      boost += 0.3;
    }

    // Company exact match
    if (job.company.toLowerCase().includes(queryLower)) {
      boost += 0.2;
    }

    // Description exact match
    if (job.description?.toLowerCase().includes(queryLower)) {
      boost += 0.1;
    }

    return boost;
  }

  private calculateSkillMatchBoost(job: Job, queryTerms: string[]): number {
    if (!job.skills_required || job.skills_required.length === 0) return 0;

    const jobSkills = job.skills_required.map(skill => 
      TextProcessor.processText(skill.toLowerCase())
    ).flat();

    let skillMatches = 0;
    queryTerms.forEach(queryTerm => {
      if (jobSkills.some(skill => skill.includes(queryTerm) || queryTerm.includes(skill))) {
        skillMatches++;
      }
    });

    return (skillMatches / queryTerms.length) * 0.2;
  }

  private calculateRecencyBoost(job: Job): number {
    const daysSincePosted = (Date.now() - new Date(job.created_at).getTime()) / (1000 * 60 * 60 * 24);
    
    if (daysSincePosted <= 7) return 0.1;
    if (daysSincePosted <= 30) return 0.05;
    if (daysSincePosted <= 90) return 0.02;
    return 0;
  }

  private calculateRemoteWorkBoost(job: Job): number {
    // Boost jobs that explicitly mention remote work
    const jobText = this.getJobText(job).toLowerCase();
    const remoteKeywords = [
      'remote', 'distributed', 'work from home', 'wfh', 'telecommute', 
      'virtual', 'online', 'location-agnostic', 'anywhere', 'global', 
      'international', 'worldwide', 'timezone', 'async'
    ];
    
    let boost = 0;
    remoteKeywords.forEach(keyword => {
      if (jobText.includes(keyword)) {
        boost += 0.05; // Small boost for each remote keyword
      }
    });
    
    // Extra boost if job is explicitly marked as remote
    if (job.remote_type === 'remote' || job.remote_type === 'fully_remote') {
      boost += 0.1;
    }
    
    return Math.min(boost, 0.3); // Cap at 0.3
  }

  // Advanced filtering with semantic understanding
  filterBySemanticMeaning(jobs: Job[], query: string): Job[] {
    const queryTerms = TextProcessor.processText(query);
    
    return jobs.filter(job => {
      const jobText = this.getJobText(job);
      const jobTerms = TextProcessor.processText(jobText);
      
      // Check for semantic similarity
      const hasSemanticMatch = queryTerms.some(queryTerm => 
        jobTerms.some(jobTerm => 
          this.areSemanticallySimilar(queryTerm, jobTerm)
        )
      );

      return hasSemanticMatch;
    });
  }

  private areSemanticallySimilar(term1: string, term2: string): boolean {
    // Simple semantic similarity based on common tech terms and remote work
    const semanticGroups = [
      ['javascript', 'js', 'node', 'react', 'vue', 'angular', 'frontend', 'web'],
      ['python', 'django', 'flask', 'fastapi', 'data', 'ml', 'ai'],
      ['java', 'spring', 'backend', 'microservices'],
      ['devops', 'docker', 'kubernetes', 'aws', 'cloud', 'infrastructure'],
      ['mobile', 'ios', 'android', 'react-native', 'flutter'],
      ['database', 'sql', 'postgresql', 'mongodb', 'redis'],
      ['remote', 'work', 'home', 'distributed', 'telecommute', 'virtual', 'online', 'digital', 'location-agnostic', 'anywhere', 'global', 'international'],
      ['senior', 'lead', 'principal', 'architect', 'experienced'],
      ['junior', 'entry', 'graduate', 'intern', 'trainee']
    ];

    for (const group of semanticGroups) {
      if (group.includes(term1) && group.includes(term2)) {
        return true;
      }
    }

    // Check for substring matches
    return term1.includes(term2) || term2.includes(term1);
  }
}

// Main search function
export function intelligentSearch(jobs: Job[], query: string): Job[] {
  const searchEngine = new IntelligentSearch(jobs);
  return searchEngine.search(query);
}
