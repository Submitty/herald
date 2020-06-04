import fs from 'fs';
import path from 'path';

import { program } from 'commander';
import fetch from 'node-fetch';

const packagePath = fs.existsSync(path.join(__dirname, 'package.json')) ? path.join(__dirname, 'package.json') : path.join(__dirname, '..', 'package.json');
const packageInfo: {version: string} = JSON.parse(fs.readFileSync(packagePath, {encoding: 'utf8'}));

const API_BASE = 'https://api.github.com/repos/';

program
  .version(packageInfo.version)
  .description('Generates changelog for a GitHub repository')
  .option('--to <tag>', 'Release tag to compare up to. Defaults to HEAD of master.', 'master')
  .option('--from <tag>', 'Release tag to compare from. Defaults to last release.');

program.parse(process.argv);

if (!fs.existsSync(path.join(process.cwd(), '.git', 'config'))) {
  console.error('Could not find .git/config file');
  process.exit(1);
}

const repoRegExp = fs.readFileSync(path.join(process.cwd(), '.git', 'config'), {encoding: 'utf8'}).match(/github\.com[:\/]([\w\d\-_]+\/[\w\d\-_]+)/);
if (!repoRegExp) {
  console.error('Could not find github remote');
  process.exit(1);
}

const repo = repoRegExp[1];

const API_URL = API_BASE + repo;
const TYPE_REGEX = /^\[([a-zA-Z0-9\/ ]+):?([a-zA-Z0-9\/ ]*)\](.*)/;

async function getCompareCommits(fromTag: string, toTag: string): Promise<{commit: {message: string}}[]> {
  const json = await fetch(API_URL + `/compare/${fromTag}...${toTag}`).then(res => res.json());
  if (json.message && !json.commits) {
    throw new Error(json.message + ' ' + json.documentation_url);
  }
  return json.commits;
}

async function getFromTag(fromTag: string | undefined) {
  return await fetch(API_URL + `/releases/${fromTag || 'latest'}`).then(res => res.json());
}

function getCommitDetails(message: string, commitTypes: string[]): {
  message: string,
  commitType: string
} {
    const lines = message.split(/\n|\r\n|\r/);
    const commitMessage = lines[0].trim();
    let commitCategory = null;
    let commitType = 'Bugfix';
    let commitSubtype = '';
    message = commitMessage;
    try {
      const match = commitMessage.match(TYPE_REGEX);
      if (!match) {
        throw new Error('Failed to parse commit message');
      }

      commitType = match[1].replace(' ', '');
      commitSubtype = match[2].replace(' ', '');
      message = match[3].trim();
      if (commitSubtype.endsWith('IU')) {
        commitSubtype = commitSubtype.substring(0, commitType.length - 2) + 'UI';
      }
      else if (commitSubtype.toLowerCase() === 'submissions') {
        commitSubtype = 'Submission';
      }
      if (['ui', 'ui/ux'].includes(commitType.toLowerCase())) {
        commitType = 'Feature';
        if (commitSubtype === '') {
          commitSubtype = 'UI/UX';
        }
      }
      else if (['testing', 'test', 'tests', 'vagrant'].includes(commitSubtype.toLowerCase())) {
        commitSubtype = 'Testing';
      }
      else if (['devdependency', 'dependencydev'].includes(commitType.toLowerCase())) {
        commitType = 'DevDependency';
        commitCategory = 'dependency';
      }
      else if (!commitTypes.includes(commitType.toLowerCase())) {
        commitType = commitSubtype === '' ? 'Bugfix' : commitSubtype;
      }
      else if (commitSubtype === 'testing') {
        commitSubtype = commitType;
        commitType = 'Testing';
      }
    }
    catch (exc) {
      commitType = 'Bugfix';
    }

    let finalMessage = `[${commitType}`;
    if (commitSubtype !== '') {
      finalMessage += `:${commitSubtype}`;
    }
    finalMessage += `] ${message}`;

    return {
      message: finalMessage,
      commitType: commitCategory ? commitCategory : commitType.toLowerCase()
    };
  }


const releaseCommits: {[key: string]: {title: string, commits: string[]}} = {
  "security": {
      "title": "SECURITY",
      "commits": []
  },
  "breaking": {
      "title": "BREAKING",
      "commits": []
  },
  "feature": {
      "title": "FEATURE / ENHANCEMENT",
      "commits": []
  },
  "vpat": {
      "title": "UI / UX",
      "commits": []
  },
  "bugfix": {
      "title": "BUGFIX",
      "commits": []
  },
  "refactor": {
      "title": "REFACTOR",
      "commits": []
  },
  "dependency": {
      "title": "SUPPORTING REPOSITORIES & VENDOR PACKAGES",
      "commits": []
  },
  "testing": {
      "title": "TESTING / BUILD",
      "commits": []
  },
  "documentation": {
      "title": "DOCUMENTATION",
      "commits": []
  }
}

getFromTag(program.from).then(async (fromTag) => {
  const commits = await getCompareCommits(fromTag.tag_name, program.to);
  const releaseCommitsKeys = Object.keys(releaseCommits);
  for (const commit of commits) {
    const {message, commitType} = getCommitDetails(commit.commit.message, releaseCommitsKeys);
    if (!releaseCommits[commitType]) {
      throw new Error(`Invalid commit type '${commitType}' from '${commit.commit.message}`);
    }
    releaseCommits[commitType].commits.push(message);
  }

  let releaseNotes = '';

  const previousLink = `[${fromTag.tag_name}](${fromTag.html_url})`;
  releaseNotes += `*Previous Release Notes:* ${previousLink}\n`;
  releaseNotes += "\n";
  for (const releaseType in releaseCommits) {
    releaseNotes += `${releaseCommits[releaseType].title}\n\n`;
    if (releaseCommits[releaseType].commits.length === 0) {
      releaseNotes += "*None*\n";
    }
    else {
      for (const commit of releaseCommits[releaseType].commits.sort()) {
        releaseNotes += `* ${commit}\n`;
      }
    }
    releaseNotes += "\n";
  }
  console.log(releaseNotes);
}).catch((err) => {
  console.error(`${err}`);
});