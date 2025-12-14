# workflow/rules/provenance.smk
# Provenance Tracking Rule - W3C PROV Compliant

import os
import sys
from pathlib import Path

rule generate_provenance:
    """
    Generate W3C PROV provenance information for the workflow.
    
    This rule generates comprehensive provenance information following W3C PROV
    standards, tracking entities, activities, agents, and their relationships.
    """
    input:
        raw_data="data/raw/tft_collection_{date}.json",
        validated_data="data/validated/tft_collection_{date}.json",
        transformed_data="data/transformed/tft_collection_{date}.jsonld",
        quality_report="reports/quality_{date}.json",
        validation_report="reports/validation_{date}.json",
        config_file="config/snakemake_config.yaml"
    output:
        provenance="provenance/workflow_{date}.prov.json"
    params:
        workflow_version="1.0.0",
        collection_date="{date}",
        base_uri=lambda wildcards: f"http://tft-data-extraction.com/workflow/{wildcards.date}"
    log:
        "logs/provenance_{date}.log"
    shell:
        """
        # Ensure output directory exists
        mkdir -p $(dirname {output.provenance})
        
        python3 -c "
import json
import sys
import hashlib
import os
import platform
import subprocess
from pathlib import Path
from datetime import datetime
from getpass import getuser

# Add project root to path
sys.path.insert(0, str(Path('{input.raw_data}').parent.parent.parent))

def calculate_file_checksum(file_path, algorithm='sha256'):
    '''Calculate SHA-256 checksum of a file'''
    if not Path(file_path).exists():
        return None
    hash_obj = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def get_file_metadata(file_path):
    '''Get file metadata including size, mtime, and checksum'''
    path = Path(file_path)
    if not path.exists():
        return None
    stat = path.stat()
    mtime_dt = datetime.fromtimestamp(stat.st_mtime)
    return {{
        'path': str(path),
        'size_bytes': stat.st_size,
        'modified_time': mtime_dt.isoformat(),
        'modified_timestamp': stat.st_mtime,  # Keep raw timestamp for calculations
        'sha256': calculate_file_checksum(file_path)
    }}

def calculate_activity_times(input_metadata, output_metadata, fallback_start=None):
    '''Calculate activity start and end times from file metadata'''
    # Start time: when input file was created (or fallback)
    if input_metadata and input_metadata.get('modified_timestamp'):
        start_time = datetime.fromtimestamp(input_metadata['modified_timestamp'])
    elif fallback_start:
        start_time = fallback_start
    else:
        start_time = None
    
    # End time: when output file was created
    if output_metadata and output_metadata.get('modified_timestamp'):
        end_time = datetime.fromtimestamp(output_metadata['modified_timestamp'])
    else:
        end_time = None
    
    # Calculate duration if both times available
    duration_seconds = None
    if start_time and end_time:
        duration_seconds = (end_time - start_time).total_seconds()
    
    return {{
        'started_at_time': start_time.isoformat() if start_time else None,
        'ended_at_time': end_time.isoformat() if end_time else None,
        'duration_seconds': duration_seconds
    }}

def get_snakemake_version():
    '''Get Snakemake version'''
    try:
        result = subprocess.run(['snakemake', '--version'], 
                              capture_output=True, text=True, timeout=5)
        return result.stdout.strip() if result.returncode == 0 else 'unknown'
    except:
        return 'unknown'

def get_python_version():
    '''Get Python version'''
    return sys.version.split()[0]

def get_git_info():
    '''Get Git version control information'''
    git_info = {{
        'commit_hash': None,
        'branch': None,
        'tag': None,
        'remote_url': None,
        'is_dirty': False,
        'available': False
    }}
    
    try:
        # Check if we're in a git repository
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=Path.cwd()
        )
        
        if result.returncode != 0:
            return git_info  # Not a git repository
        
        git_info['available'] = True
        
        # Get commit hash
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=Path.cwd()
            )
            if result.returncode == 0:
                git_info['commit_hash'] = result.stdout.strip()
        except:
            pass
        
        # Get branch name
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=Path.cwd()
            )
            if result.returncode == 0:
                branch = result.stdout.strip()
                # Handle detached HEAD state
                if branch != 'HEAD':
                    git_info['branch'] = branch
        except:
            pass
        
        # Get tag (if any)
        try:
            result = subprocess.run(
                ['git', 'describe', '--tags', '--always', '--exact-match'],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=Path.cwd()
            )
            if result.returncode == 0:
                tag = result.stdout.strip()
                # Only use if it's actually a tag (not a commit hash)
                if not tag.startswith(git_info.get('commit_hash', '')[:7]):
                    git_info['tag'] = tag
        except:
            pass
        
        # Get remote URL
        try:
            result = subprocess.run(
                ['git', 'config', '--get', 'remote.origin.url'],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=Path.cwd()
            )
            if result.returncode == 0:
                git_info['remote_url'] = result.stdout.strip()
        except:
            pass
        
        # Check if working directory is dirty (uncommitted changes)
        try:
            result = subprocess.run(
                ['git', 'diff', '--quiet', 'HEAD'],
                capture_output=True,
                timeout=5,
                cwd=Path.cwd()
            )
            git_info['is_dirty'] = (result.returncode != 0)
        except:
            pass
            
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        # Git not available or error occurred
        pass
    
    return git_info

try:
    base_uri = '{params.base_uri}'
    collection_date = '{params.collection_date}'
    workflow_version = '{params.workflow_version}'
    
    # Get system information
    snakemake_version = get_snakemake_version()
    python_version = get_python_version()
    user = getuser()
    hostname = platform.node()
    platform_info = platform.platform()
    
    # Get Git version control information
    git_info = get_git_info()
    
    # Get file metadata for all inputs and outputs
    raw_metadata = get_file_metadata('{input.raw_data}')
    validated_metadata = get_file_metadata('{input.validated_data}')
    transformed_metadata = get_file_metadata('{input.transformed_data}')
    quality_metadata = get_file_metadata('{input.quality_report}')
    validation_metadata = get_file_metadata('{input.validation_report}')
    config_metadata = get_file_metadata('{input.config_file}')
    
    # Load quality report if available
    quality_data = None
    if quality_metadata and quality_metadata.get('path'):
        try:
            with open(quality_metadata['path'], 'r') as f:
                quality_data = json.load(f)
        except:
            pass
    
    # Load validation report if available
    validation_data = None
    if validation_metadata and validation_metadata.get('path'):
        try:
            with open(validation_metadata['path'], 'r') as f:
                validation_data = json.load(f)
        except:
            pass
    
    # Extract error summary from raw data if available
    error_summary = None
    collection_info = None
    if raw_metadata and raw_metadata.get('path'):
        try:
            with open(raw_metadata['path'], 'r') as f:
                raw_data = json.load(f)
                # Check for error_summary at top level
                error_summary = raw_data.get('error_summary')
                # Get collectionInfo for API endpoint tracking
                collection_info = raw_data.get('collectionInfo', {{}})
                # Also check in collectionInfo for error_summary
                if not error_summary and collection_info:
                    if 'error_summary' in collection_info:
                        error_summary = collection_info['error_summary']
        except:
            pass
    
    # Extract Python package versions
    def get_python_package_versions():
        '''Get installed Python package versions'''
        package_versions = {{}}
        try:
            # Try to get versions from installed packages
            import importlib.metadata
            packages = ['duckdb', 'requests', 'networkx', 'python-dotenv', 'pandas', 'numpy', 'pytest', 'pytest-asyncio', 'snakemake', 'pyyaml']
            for package in packages:
                try:
                    version = importlib.metadata.version(package)
                    package_versions[package] = version
                except:
                    # Try alternative import method
                    try:
                        mod = __import__(package.replace('-', '_'))
                        if hasattr(mod, '__version__'):
                            package_versions[package] = mod.__version__
                    except:
                        pass
        except ImportError:
            # Fallback: try reading requirements.txt
            try:
                req_path = Path('requirements.txt')
                if req_path.exists():
                    with open(req_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                parts = line.split('>=')
                                if len(parts) == 2:
                                    package_versions[parts[0].strip()] = parts[1].strip()
            except:
                pass
        return package_versions
    
    # Get API endpoint information
    def get_api_endpoint_info():
        '''Extract API endpoint usage information'''
        api_info = {{
            'base_urls': [],
            'endpoints_used': [],
            'region': None,
            'api_version': None
        }}
        
        # Extract from collectionInfo if available
        if collection_info:
            api_info['region'] = collection_info.get('extractionLocation')
            api_info['api_version'] = collection_info.get('dataVersion')
        
        # Get known API endpoints from documentation
        try:
            from scripts.riot_api_endpoints import API_ENDPOINTS_DOCUMENTATION
            for category, info in API_ENDPOINTS_DOCUMENTATION.items():
                if 'endpoints' in info:
                    api_info['endpoints_used'].extend(info['endpoints'])
        except:
            # Fallback: common Riot API endpoints
            api_info['endpoints_used'] = [
                '/tft/match/v1/matches/by-puuid/{{puuid}}/ids',
                '/tft/match/v1/matches/{{matchId}}',
                '/tft/summoner/v1/summoners/by-puuid/{{encryptedPUUID}}',
                '/tft/league/v1/challenger',
                '/tft/league/v1/grandmaster',
                '/tft/league/v1/master'
            ]
        
        # Add base URLs
        api_info['base_urls'] = [
            'https://la2.api.riotgames.com',
            'https://americas.api.riotgames.com'
        ]
        
        return api_info
    
    python_packages = get_python_package_versions()
    api_endpoint_info = get_api_endpoint_info()
    
    # Load config if available
    config_data = None
    if config_metadata and config_metadata.get('path'):
        try:
            try:
                import yaml
                with open(config_metadata['path'], 'r') as f:
                    config_data = yaml.safe_load(f)
            except ImportError:
                # Fallback: read as JSON if YAML not available
                with open(config_metadata['path'], 'r') as f:
                    config_data = {{'config_file': config_metadata['path']}}
        except:
            pass
    
    # Try to create dataset identifier using identifier system
    dataset_id = None
    try:
        from scripts.identifier_system import TFTIdentifierSystem
        identifier_system = TFTIdentifierSystem()
        # Create dataset identifier from transformed data
        if transformed_metadata and transformed_metadata.get('path'):
            try:
                with open(transformed_metadata['path'], 'r') as f:
                    dataset_data = json.load(f)
                dataset_id = identifier_system.create_dataset_identifier(dataset_data)
            except:
                pass
    except ImportError:
        pass
    except Exception:
        pass
    
    # Check if backup exists
    backup_path = f'backups/backup_{{collection_date}}.tar.gz'
    backup_metadata = get_file_metadata(backup_path) if Path(backup_path).exists() else None
    
    # Generate unique IDs for PROV entities
    entity_ids = {{
        'raw_data': f'{{base_uri}}/entity/raw_data',
        'validated_data': f'{{base_uri}}/entity/validated_data',
        'transformed_data': f'{{base_uri}}/entity/transformed_data',
        'quality_report': f'{{base_uri}}/entity/quality_report',
        'validation_report': f'{{base_uri}}/entity/validation_report',
        'config': f'{{base_uri}}/entity/config',
        'provenance': f'{{base_uri}}/entity/provenance'
    }}
    
    # Generate error entity IDs if errors exist
    error_entities = []
    error_entity_ids = {{}}
    if error_summary and error_summary.get('total_errors', 0) > 0:
        errors_by_category = error_summary.get('errors_by_category', {{}})
        for category, error_info in errors_by_category.items():
            error_id = f'{{base_uri}}/entity/error_{{category}}'
            error_entity_ids[category] = error_id
            error_entities.append({{
                '@id': error_id,
                '@type': 'prov:Entity',
                'prov:label': f'Collection Error: {{category}}',
                'dcterms:title': f'{{category}} Errors',
                'dcterms:description': f'Errors encountered during data collection',
                'tft:error_category': category,
                'tft:error_count': error_info.get('count', 0),
                'tft:failed_match_count': len(error_info.get('match_ids', [])),
                'tft:failed_player_count': len(error_info.get('player_puuids', [])),
                'tft:failed_match_ids_sample': error_info.get('match_ids', [])[:10],  # Summary only
                'tft:failed_player_puuids_sample': error_info.get('player_puuids', [])[:10]  # Summary only
            }})
    
    # Generate dependency entity IDs
    dependency_entities = []
    dependency_entity_ids = {{}}
    
    # Python package dependencies
    for package_name, package_version in python_packages.items():
        dep_id = f'{{base_uri}}/entity/dependency/python_{{package_name}}'
        dependency_entity_ids[f'python_{{package_name}}'] = dep_id
        dependency_entities.append({{
            '@id': dep_id,
            '@type': 'prov:Entity',
            'prov:label': f'Python Package: {{package_name}}',
            'dcterms:title': f'{{package_name}} Python Package',
            'dcterms:description': f'Python package dependency used in workflow',
            'tft:package_name': package_name,
            'tft:package_version': package_version,
            'tft:package_type': 'python',
            'tft:dependency_type': 'software'
        }})
    
    # API endpoint dependencies
    if api_endpoint_info.get('base_urls'):
        api_dep_id = f'{{base_uri}}/entity/dependency/api_riot_games'
        dependency_entity_ids['api_riot_games'] = api_dep_id
        dependency_entities.append({{
            '@id': api_dep_id,
            '@type': 'prov:Entity',
            'prov:label': 'Riot Games API',
            'dcterms:title': 'Riot Games TFT API',
            'dcterms:description': 'External API service used for data collection',
            'tft:api_name': 'Riot Games TFT API',
            'tft:api_region': api_endpoint_info.get('region'),
            'tft:api_version': api_endpoint_info.get('api_version'),
            'tft:base_urls': api_endpoint_info.get('base_urls', []),
            'tft:endpoints_used': api_endpoint_info.get('endpoints_used', [])[:20],  # Limit to 20 endpoints
            'tft:endpoint_count': len(api_endpoint_info.get('endpoints_used', [])),
            'tft:dependency_type': 'external_api'
        }})
    
    if backup_metadata:
        entity_ids['backup'] = f'{{base_uri}}/entity/backup'
    
    # Generate unique IDs for PROV activities
    activity_ids = {{
        'collection': f'{{base_uri}}/activity/collection',
        'validation': f'{{base_uri}}/activity/validation',
        'transformation': f'{{base_uri}}/activity/transformation',
        'quality_assessment': f'{{base_uri}}/activity/quality_assessment',
        'provenance_generation': f'{{base_uri}}/activity/provenance_generation',
        'workflow_execution': f'{{base_uri}}/activity/workflow_execution'
    }}
    
    # Generate unique IDs for PROV agents
    agent_ids = {{
        'snakemake': f'{{base_uri}}/agent/snakemake',
        'workflow_system': f'{{base_uri}}/agent/workflow_system',
        'user': f'{{base_uri}}/agent/user',
        'api_source': 'https://developer.riotgames.com/'
    }}
    
    execution_time = datetime.now().isoformat()
    current_time = datetime.now()
    
    # Calculate activity times from file metadata
    # Collection: starts when config is read, ends when raw_data is created
    collection_times = calculate_activity_times(
        config_metadata, 
        raw_metadata, 
        fallback_start=current_time
    )
    
    # Validation: starts when raw_data exists, ends when validated_data is created
    validation_times = calculate_activity_times(
        raw_metadata,
        validated_metadata
    )
    
    # Transformation: starts when validated_data exists, ends when transformed_data is created
    transformation_times = calculate_activity_times(
        validated_metadata,
        transformed_metadata
    )
    
    # Quality assessment: starts when transformed_data exists, ends when quality_report is created
    quality_times = calculate_activity_times(
        transformed_metadata,
        quality_metadata
    )
    
    # Provenance generation: starts after all outputs exist, ends now
    # Use the latest file modification time as start
    latest_file_time = None
    for metadata in [raw_metadata, validated_metadata, transformed_metadata, quality_metadata, validation_metadata]:
        if metadata and metadata.get('modified_timestamp'):
            if latest_file_time is None or metadata['modified_timestamp'] > latest_file_time:
                latest_file_time = metadata['modified_timestamp']
    
    provenance_start = datetime.fromtimestamp(latest_file_time) if latest_file_time else current_time
    provenance_times = {{
        'started_at_time': provenance_start.isoformat(),
        'ended_at_time': current_time.isoformat(),
        'duration_seconds': (current_time - provenance_start).total_seconds()
    }}
    
    # Workflow execution: from earliest to latest
    workflow_start = None
    workflow_end = None
    for metadata in [raw_metadata, validated_metadata, transformed_metadata, quality_metadata, validation_metadata]:
        if metadata and metadata.get('modified_timestamp'):
            mtime = datetime.fromtimestamp(metadata['modified_timestamp'])
            if workflow_start is None or mtime < workflow_start:
                workflow_start = mtime
            if workflow_end is None or mtime > workflow_end:
                workflow_end = mtime
    
    workflow_times = {{
        'started_at_time': workflow_start.isoformat() if workflow_start else current_time.isoformat(),
        'ended_at_time': workflow_end.isoformat() if workflow_end else current_time.isoformat(),
        'duration_seconds': (workflow_end - workflow_start).total_seconds() if (workflow_start and workflow_end) else None
    }}
    
    # Generate error relationships if errors exist
    error_was_generated_by = []
    error_was_influenced_by = []
    if error_entity_ids:
        for category in error_entity_ids:
            error_was_generated_by.append({{
                '@id': f'{{base_uri}}/wasGeneratedBy/error_{{category}}',
                'prov:entity': error_entity_ids[category],
                'prov:activity': activity_ids['collection'],
                'prov:time': collection_times['ended_at_time'] or execution_time
            }})
            error_was_influenced_by.append({{
                '@id': f'{{base_uri}}/wasInfluencedBy/error_{{category}}',
                'prov:activity': activity_ids['collection'],
                'prov:entity': error_entity_ids[category],
                'prov:time': collection_times['ended_at_time'] or execution_time
            }})
    
    # Generate dependency relationships
    dependency_used_relationships = []
    if 'api_riot_games' in dependency_entity_ids:
        dependency_used_relationships.append({{
            '@id': f'{{base_uri}}/used/collection_api',
            'prov:activity': activity_ids['collection'],
            'prov:entity': dependency_entity_ids['api_riot_games'],
            'prov:time': collection_times['started_at_time'] or execution_time
        }})
    
    for package in python_packages.keys():
        dep_key = f'python_{{package}}'
        if dep_key in dependency_entity_ids:
            dependency_used_relationships.append({{
                '@id': f'{{base_uri}}/used/workflow_python_{{package}}',
                'prov:activity': activity_ids['workflow_execution'],
                'prov:entity': dependency_entity_ids[dep_key],
                'prov:time': workflow_times['started_at_time'] or execution_time
            }})
    
    # Build W3C PROV compliant provenance document
    provenance = {{
        '@context': {{
            'prov': 'http://www.w3.org/ns/prov#',
            'xsd': 'http://www.w3.org/2001/XMLSchema#',
            'dcterms': 'http://purl.org/dc/terms/',
            'tft': 'http://tft-data-extraction.com/schema#'
        }},
        '@type': 'prov:Bundle',
        'prefix': {{
            'prov': 'http://www.w3.org/ns/prov#',
            'tft': 'http://tft-data-extraction.com/schema#'
        }},
        'entity': [
            {{
                '@id': entity_ids['raw_data'],
                '@type': 'prov:Entity',
                'prov:label': 'Raw TFT Collection Data',
                'dcterms:title': 'Raw TFT Collection Data',
                'dcterms:description': 'Raw match data collected from Riot API',
                'prov:value': raw_metadata['path'] if raw_metadata else None,
                'tft:file_size': raw_metadata['size_bytes'] if raw_metadata else None,
                'tft:sha256': raw_metadata['sha256'] if raw_metadata else None,
                'tft:modified_time': raw_metadata['modified_time'] if raw_metadata else None,
                'tft:collection_date': collection_date
            }},
            {{
                '@id': entity_ids['validated_data'],
                '@type': 'prov:Entity',
                'prov:label': 'Validated TFT Collection Data',
                'dcterms:title': 'Validated TFT Collection Data',
                'dcterms:description': 'Validated and quality-checked match data',
                'prov:value': validated_metadata['path'] if validated_metadata else None,
                'tft:file_size': validated_metadata['size_bytes'] if validated_metadata else None,
                'tft:sha256': validated_metadata['sha256'] if validated_metadata else None,
                'tft:modified_time': validated_metadata['modified_time'] if validated_metadata else None
            }},
            {{
                '@id': entity_ids['transformed_data'],
                '@type': 'prov:Entity',
                'prov:label': 'Transformed JSON-LD Data',
                'dcterms:title': 'Transformed JSON-LD Data',
                'dcterms:description': 'Data transformed to JSON-LD format with semantic annotations',
                'prov:value': transformed_metadata['path'] if transformed_metadata else None,
                'tft:file_size': transformed_metadata['size_bytes'] if transformed_metadata else None,
                'tft:sha256': transformed_metadata['sha256'] if transformed_metadata else None,
                'tft:modified_time': transformed_metadata['modified_time'] if transformed_metadata else None,
                'tft:format': 'JSON-LD'
            }},
            {{
                '@id': entity_ids['quality_report'],
                '@type': 'prov:Entity',
                'prov:label': 'Quality Assessment Report',
                'dcterms:title': 'Quality Assessment Report',
                'dcterms:description': 'Data quality metrics and validation results',
                'prov:value': quality_metadata['path'] if quality_metadata else None,
                'tft:file_size': quality_metadata['size_bytes'] if quality_metadata else None,
                'tft:sha256': quality_metadata['sha256'] if quality_metadata else None,
                'tft:modified_time': quality_metadata['modified_time'] if quality_metadata else None,
                'tft:quality_metrics': quality_data if quality_data else None
            }},
            {{
                '@id': entity_ids['validation_report'],
                '@type': 'prov:Entity',
                'prov:label': 'Validation Report',
                'dcterms:title': 'Data Validation Report',
                'dcterms:description': 'Data validation results and quality threshold check',
                'prov:value': validation_metadata['path'] if validation_metadata else None,
                'tft:file_size': validation_metadata['size_bytes'] if validation_metadata else None,
                'tft:sha256': validation_metadata['sha256'] if validation_metadata else None,
                'tft:modified_time': validation_metadata['modified_time'] if validation_metadata else None,
                'tft:validation_results': validation_data if validation_data else None
            }},
            {{
                '@id': entity_ids['config'],
                '@type': 'prov:Entity',
                'prov:label': 'Workflow Configuration',
                'dcterms:title': 'Snakemake Workflow Configuration',
                'dcterms:description': 'Configuration parameters used for workflow execution',
                'prov:value': config_metadata['path'] if config_metadata else None,
                'tft:file_size': config_metadata['size_bytes'] if config_metadata else None,
                'tft:sha256': config_metadata['sha256'] if config_metadata else None,
                'tft:config_content': config_data if config_data else None
            }},
            {{
                '@id': entity_ids['provenance'],
                '@type': 'prov:Entity',
                'prov:label': 'Provenance Document',
                'dcterms:title': 'Workflow Provenance Document',
                'dcterms:description': 'This provenance document',
                'prov:value': '{output.provenance}',
                'tft:format': 'W3C PROV JSON-LD'
            }}
        ] + error_entities + dependency_entities + ([{{
                '@id': entity_ids['backup'],
                '@type': 'prov:Entity',
                'prov:label': 'Backup Archive',
                'dcterms:title': 'Workflow Backup Archive',
                'dcterms:description': 'Compressed backup archive of workflow outputs',
                'prov:value': backup_metadata['path'] if backup_metadata else None,
                'tft:file_size': backup_metadata['size_bytes'] if backup_metadata else None,
                'tft:sha256': backup_metadata['sha256'] if backup_metadata else None,
                'tft:modified_time': backup_metadata['modified_time'] if backup_metadata else None,
                'tft:format': 'tar.gz'
            }}] if backup_metadata else []),
        'activity': [
            {{
                '@id': activity_ids['collection'],
                '@type': 'prov:Activity',
                'prov:label': 'Data Collection',
                'dcterms:title': 'TFT Match Data Collection',
                'dcterms:description': 'Collection of TFT match data from Riot API',
                'prov:startedAtTime': collection_times['started_at_time'] or execution_time,
                'prov:endedAtTime': collection_times['ended_at_time'],
                'tft:duration_seconds': collection_times['duration_seconds'],
                'tft:workflow_step': 'collect_tft_data',
                'tft:collection_date': collection_date,
                'tft:total_errors': error_summary.get('total_errors', 0) if error_summary else 0,
                'tft:error_categories': list(error_summary.get('errors_by_category', {{}}).keys()) if error_summary else []
            }},
            {{
                '@id': activity_ids['validation'],
                '@type': 'prov:Activity',
                'prov:label': 'Data Validation',
                'dcterms:title': 'Data Quality Validation',
                'dcterms:description': 'Validation of collected data against schemas and quality checks',
                'prov:startedAtTime': validation_times['started_at_time'] or execution_time,
                'prov:endedAtTime': validation_times['ended_at_time'],
                'tft:duration_seconds': validation_times['duration_seconds'],
                'tft:workflow_step': 'validate_collection'
            }},
            {{
                '@id': activity_ids['transformation'],
                '@type': 'prov:Activity',
                'prov:label': 'Data Transformation',
                'dcterms:title': 'JSON-LD Transformation',
                'dcterms:description': 'Transformation of validated data to JSON-LD format',
                'prov:startedAtTime': transformation_times['started_at_time'] or execution_time,
                'prov:endedAtTime': transformation_times['ended_at_time'],
                'tft:duration_seconds': transformation_times['duration_seconds'],
                'tft:workflow_step': 'transform_to_jsonld'
            }},
            {{
                '@id': activity_ids['quality_assessment'],
                '@type': 'prov:Activity',
                'prov:label': 'Quality Assessment',
                'dcterms:title': 'Quality Metrics Calculation',
                'dcterms:description': 'Calculation of data quality metrics and anomaly detection',
                'prov:startedAtTime': quality_times['started_at_time'] or execution_time,
                'prov:endedAtTime': quality_times['ended_at_time'],
                'tft:duration_seconds': quality_times['duration_seconds'],
                'tft:workflow_step': 'calculate_quality_metrics'
            }},
            {{
                '@id': activity_ids['provenance_generation'],
                '@type': 'prov:Activity',
                'prov:label': 'Provenance Generation',
                'dcterms:title': 'Provenance Document Generation',
                'dcterms:description': 'Generation of this provenance document',
                'prov:startedAtTime': provenance_times['started_at_time'],
                'prov:endedAtTime': provenance_times['ended_at_time'],
                'tft:duration_seconds': provenance_times['duration_seconds'],
                'tft:workflow_step': 'generate_provenance'
            }},
            {{
                '@id': activity_ids['workflow_execution'],
                '@type': 'prov:Activity',
                'prov:label': 'Workflow Execution',
                'dcterms:title': 'Complete Workflow Execution',
                'dcterms:description': 'End-to-end workflow execution',
                'prov:startedAtTime': workflow_times['started_at_time'],
                'prov:endedAtTime': workflow_times['ended_at_time'],
                'tft:duration_seconds': workflow_times['duration_seconds'],
                'tft:workflow_version': workflow_version,
                'tft:collection_date': collection_date
            }}
        ],
        'agent': [
            {{
                '@id': agent_ids['snakemake'],
                '@type': 'prov:SoftwareAgent',
                'prov:label': 'Snakemake',
                'dcterms:title': 'Snakemake Workflow Management System',
                'dcterms:description': 'Workflow management system used to execute the pipeline',
                'tft:version': snakemake_version,
                'tft:type': 'workflow_engine'
            }},
            {{
                '@id': agent_ids['workflow_system'],
                '@type': 'prov:SoftwareAgent',
                'prov:label': 'TFT Data Curation Workflow',
                'dcterms:title': 'TFT Data Curation Workflow System',
                'dcterms:description': 'Automated workflow system for TFT data collection and curation',
                'tft:version': workflow_version,
                'tft:python_version': python_version,
                'tft:platform': platform_info
            }},
            {{
                '@id': agent_ids['user'],
                '@type': 'prov:Person',
                'prov:label': f'User: {{user}}',
                'dcterms:title': f'Workflow Executor: {{user}}',
                'dcterms:description': 'User who executed the workflow',
                'tft:username': user,
                'tft:hostname': hostname
            }},
            {{
                '@id': agent_ids['api_source'],
                '@type': 'prov:Organization',
                'prov:label': 'Riot Games API',
                'dcterms:title': 'Riot Games Developer API',
                'dcterms:description': 'Source of TFT match data via Riot Games API',
                'tft:api_endpoint': 'https://developer.riotgames.com/'
            }}
        ],
        'wasGeneratedBy': [
            {{
                '@id': f'{{base_uri}}/wasGeneratedBy/raw_data',
                'prov:entity': entity_ids['raw_data'],
                'prov:activity': activity_ids['collection'],
                'prov:time': collection_times['ended_at_time'] or execution_time
            }},
            {{
                '@id': f'{{base_uri}}/wasGeneratedBy/validated_data',
                'prov:entity': entity_ids['validated_data'],
                'prov:activity': activity_ids['validation'],
                'prov:time': validation_times['ended_at_time'] or execution_time
            }},
            {{
                '@id': f'{{base_uri}}/wasGeneratedBy/transformed_data',
                'prov:entity': entity_ids['transformed_data'],
                'prov:activity': activity_ids['transformation'],
                'prov:time': transformation_times['ended_at_time'] or execution_time
            }},
            {{
                '@id': f'{{base_uri}}/wasGeneratedBy/quality_report',
                'prov:entity': entity_ids['quality_report'],
                'prov:activity': activity_ids['quality_assessment'],
                'prov:time': quality_times['ended_at_time'] or execution_time
            }},
            {{
                '@id': f'{{base_uri}}/wasGeneratedBy/provenance',
                'prov:entity': entity_ids['provenance'],
                'prov:activity': activity_ids['provenance_generation'],
                'prov:time': provenance_times['ended_at_time']
            }}
        ] + error_was_generated_by + ([{{
                '@id': f'{{base_uri}}/wasGeneratedBy/backup',
                'prov:entity': entity_ids['backup'],
                'prov:activity': activity_ids['workflow_execution'],
                'prov:time': workflow_times['ended_at_time'] or execution_time
            }}] if backup_metadata else []),
        'used': [
            {{
                '@id': f'{{base_uri}}/used/validation',
                'prov:activity': activity_ids['validation'],
                'prov:entity': entity_ids['raw_data'],
                'prov:time': validation_times['started_at_time'] or execution_time
            }},
            {{
                '@id': f'{{base_uri}}/used/transformation',
                'prov:activity': activity_ids['transformation'],
                'prov:entity': entity_ids['validated_data'],
                'prov:time': transformation_times['started_at_time'] or execution_time
            }},
            {{
                '@id': f'{{base_uri}}/used/quality_assessment',
                'prov:activity': activity_ids['quality_assessment'],
                'prov:entity': entity_ids['transformed_data'],
                'prov:time': quality_times['started_at_time'] or execution_time
            }},
            {{
                '@id': f'{{base_uri}}/used/collection_config',
                'prov:activity': activity_ids['collection'],
                'prov:entity': entity_ids['config'],
                'prov:time': collection_times['started_at_time'] or execution_time
            }}
        ] + dependency_used_relationships,
        'wasDerivedFrom': [
            {{
                '@id': f'{{base_uri}}/wasDerivedFrom/validated_from_raw',
                'prov:generatedEntity': entity_ids['validated_data'],
                'prov:usedEntity': entity_ids['raw_data'],
                'prov:activity': activity_ids['validation'],
                'prov:time': validation_times['ended_at_time'] or execution_time
            }},
            {{
                '@id': f'{{base_uri}}/wasDerivedFrom/transformed_from_validated',
                'prov:generatedEntity': entity_ids['transformed_data'],
                'prov:usedEntity': entity_ids['validated_data'],
                'prov:activity': activity_ids['transformation'],
                'prov:time': transformation_times['ended_at_time'] or execution_time
            }}
        ] + error_was_influenced_by,
        'wasAttributedTo': [
            {{
                '@id': f'{{base_uri}}/wasAttributedTo/workflow',
                'prov:entity': entity_ids['provenance'],
                'prov:agent': agent_ids['workflow_system']
            }},
            {{
                '@id': f'{{base_uri}}/wasAttributedTo/user',
                'prov:entity': entity_ids['provenance'],
                'prov:agent': agent_ids['user']
            }},
            {{
                '@id': f'{{base_uri}}/wasAttributedTo/raw_data_source',
                'prov:entity': entity_ids['raw_data'],
                'prov:agent': agent_ids['api_source']
            }}
        ],
        'wasAssociatedWith': [
            {{
                '@id': f'{{base_uri}}/wasAssociatedWith/collection',
                'prov:activity': activity_ids['collection'],
                'prov:agent': agent_ids['snakemake']
            }},
            {{
                '@id': f'{{base_uri}}/wasAssociatedWith/validation',
                'prov:activity': activity_ids['validation'],
                'prov:agent': agent_ids['snakemake']
            }},
            {{
                '@id': f'{{base_uri}}/wasAssociatedWith/transformation',
                'prov:activity': activity_ids['transformation'],
                'prov:agent': agent_ids['snakemake']
            }},
            {{
                '@id': f'{{base_uri}}/wasAssociatedWith/quality',
                'prov:activity': activity_ids['quality_assessment'],
                'prov:agent': agent_ids['snakemake']
            }},
            {{
                '@id': f'{{base_uri}}/wasAssociatedWith/workflow',
                'prov:activity': activity_ids['workflow_execution'],
                'prov:agent': agent_ids['workflow_system']
            }}
        ],
        'wasInformedBy': [
            {{
                '@id': f'{{base_uri}}/wasInformedBy/validation',
                'prov:informant': activity_ids['validation'],
                'prov:informed': activity_ids['transformation']
            }},
            {{
                '@id': f'{{base_uri}}/wasInformedBy/transformation',
                'prov:informant': activity_ids['transformation'],
                'prov:informed': activity_ids['quality_assessment']
            }},
            {{
                '@id': f'{{base_uri}}/wasInformedBy/collection',
                'prov:informant': activity_ids['collection'],
                'prov:informed': activity_ids['validation']
            }}
        ],
        'metadata': {{
            'workflow_version': workflow_version,
            'collection_date': collection_date,
            'execution_time': execution_time,
            'snakemake_version': snakemake_version,
            'python_version': python_version,
            'platform': platform_info,
            'user': user,
            'hostname': hostname,
            'dataset_identifier': dataset_id,
            'version_control': {{
                'git_available': git_info['available'],
                'git_commit_hash': git_info['commit_hash'],
                'git_branch': git_info['branch'],
                'git_tag': git_info['tag'],
                'git_remote_url': git_info['remote_url'],
                'git_is_dirty': git_info['is_dirty']
            }},
            'workflow_steps': [
                'collect_tft_data',
                'validate_collection',
                'transform_to_jsonld',
                'calculate_quality_metrics',
                'generate_provenance'
            ]
        }}
    }}
    
    with open('{output.provenance}', 'w') as f:
        json.dump(provenance, f, indent=2, ensure_ascii=False)
    
    # Verify output file was created
    output_path = Path('{output.provenance}')
    if not output_path.exists():
        raise FileNotFoundError(f'Output file {{output_path}} was not created')
    
    print(f'[SUCCESS] W3C PROV provenance generated for collection date: {{collection_date}}')
    entity_count = len(provenance.get('entity', []))
    activity_count = len(provenance.get('activity', []))
    print(f'[SUCCESS] Output file: {{output_path}} ({{output_path.stat().st_size / 1024:.2f}} KB)')
    agent_count = len(provenance.get('agent', []))
    relationship_count = len(provenance.get('wasGeneratedBy', [])) + len(provenance.get('used', []))
    print(f'   Entities: {{entity_count}}')
    print(f'   Activities: {{activity_count}}')
    print(f'   Agents: {{agent_count}}')
    print(f'   Relationships: {{relationship_count}}')
except Exception as e:
    print(f'[ERROR] Provenance generation error: {{e}}', file=sys.stderr)
    import traceback
    traceback.print_exc()
    raise
" 2>&1 | tee {log}
        """
