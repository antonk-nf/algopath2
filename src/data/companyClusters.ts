export interface CompanyCluster {
  id: string;
  label: string;
  description: string;
  color: string;
  icon: 'Building2' | 'ShoppingBag' | 'ChartBar' | 'Briefcase' | 'Route';
  companies: string[];
}

export interface ClusterAlgorithm {
  name: string;
  clusters: CompanyCluster[];
}

export const algorithmB: ClusterAlgorithm = {
  name: 'Algorithm B',
  clusters: [
    {
      id: 'B1',
      label: 'Global Big Tech',
      description: 'Product-centric giants with massive engineering scale across cloud, mobile, and AI.',
      color: '#6366F1',
      icon: 'Building2',
      companies: [
        'Adobe','Amazon','Apple','Bloomberg','ByteDance','Cisco','Google','Intuit','Meta','Microsoft','Nvidia','Oracle','SAP','Salesforce','ServiceNow','Tesla','Visa','Walmart Labs','X','Yahoo','Yandex'
      ]
    },
    {
      id: 'B2',
      label: 'Consumer Internet & Marketplaces',
      description: 'High-growth consumer platforms and marketplaces optimizing logistics, content, and engagement.',
      color: '#F97316',
      icon: 'ShoppingBag',
      companies: [
        'Airbnb','Anduril','Citadel','Coupang','DE Shaw','Docusign','DoorDash','Flipkart','MakeMyTrip','Nutanix','Palantir Technologies','PhonePe','Samsung','Snap','Snowflake','TikTok','Uber','Wix','Zepto','eBay'
      ]
    },
    {
      id: 'B3',
      label: 'Enterprise & FinTech Innovators',
      description: 'Financial institutions and SaaS leaders modernising payments, analytics, and developer tooling.',
      color: '#10B981',
      icon: 'ChartBar',
      companies: [
        'Atlassian','Goldman Sachs','IBM','Infosys','J.P. Morgan','PayPal','Turing','Zoho'
      ]
    },
    {
      id: 'B4',
      label: 'Consulting & IT Services',
      description: 'Global consultancies delivering large-scale digital transformation and outsourcing programs.',
      color: '#0EA5E9',
      icon: 'Briefcase',
      companies: [
        'Accenture','Capgemini','Cognizant','Deloitte','EPAM Systems','tcs'
      ]
    },
    {
      id: 'B5',
      label: 'Travel & Emerging Platforms',
      description: 'Travel, commerce, and platform players expanding into new digital business lines.',
      color: '#F59E0B',
      icon: 'Route',
      companies: [
        'Agoda','Expedia','Morgan Stanley','Paytm','Swiggy'
      ]
    }
  ]
};

export const algorithms = {
  B: algorithmB
};
