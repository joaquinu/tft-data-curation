"""
This module contains the comprehensive JSON-LD schema definitions for TFT data collection.
Provides semantic data structure design and RDF compatibility for analysis-ready datasets.
"""

import json
from typing import Dict, Any
from datetime import datetime


class TFTSchemaGenerator:
    """
    Generates comprehensive JSON-LD schema for TFT data
    """
    
    def __init__(self):
        """Initialize schema generator with base URIs and namespace configuration"""
        self.base_uri = "http://tft-data-extraction.com/"
        self.schema_uri = f"{self.base_uri}schema#"
        
    def create_comprehensive_schema(self) -> Dict[str, Any]:
        """
        Create a complete JSON-LD schema for TFT data structures
        """
        
        schema = {
            "@context": {
                "@vocab": self.schema_uri,
                "@base": self.base_uri,
                "tft": self.schema_uri,
                "xsd": "http://www.w3.org/2001/XMLSchema#",
                "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "dcterms": "http://purl.org/dc/terms/",
                "foaf": "http://xmlns.com/foaf/0.1/",
                "time": "http://www.w3.org/2006/time#",
                
                "TFTDataCollection": {
                    "@type": "@id",
                    "rdfs:label": "TFT Data Collection",
                    "rdfs:comment": "A collection of TFT match and player data"
                },
                "TFTPlayer": {
                    "@type": "@id", 
                    "rdfs:label": "TFT Player",
                    "rdfs:comment": "A Teamfight Tactics player"
                },
                "TFTMatch": {
                    "@type": "@id",
                    "rdfs:label": "TFT Match", 
                    "rdfs:comment": "A Teamfight Tactics match/game"
                },
                "TFTParticipant": {
                    "@type": "@id",
                    "rdfs:label": "TFT Match Participant",
                    "rdfs:comment": "A player's participation in a specific match"
                },
                "TFTChampion": {
                    "@type": "@id",
                    "rdfs:label": "TFT Champion",
                    "rdfs:comment": "A champion unit in TFT"
                },
                "TFTTrait": {
                    "@type": "@id",
                    "rdfs:label": "TFT Trait",
                    "rdfs:comment": "A trait/synergy in TFT"
                },
                "TFTItem": {
                    "@type": "@id",
                    "rdfs:label": "TFT Item", 
                    "rdfs:comment": "An item that can be equipped on champions"
                },
                
                "puuid": {
                    "@type": "xsd:string",
                    "rdfs:label": "Player Unique ID"
                },
                "gameName": {
                    "@type": "xsd:string", 
                    "rdfs:label": "Game Name"
                },
                "tagLine": {
                    "@type": "xsd:string",
                    "rdfs:label": "Tag Line"
                },
                "extractionTimestamp": {
                    "@type": "xsd:dateTime",
                    "rdfs:label": "Extraction Timestamp"
                },
                "gameCreation": {
                    "@type": "xsd:dateTime", 
                    "rdfs:label": "Game Creation Time"
                },
                "gameLength": {
                    "@type": "xsd:float",
                    "rdfs:label": "Game Length in Seconds"
                },
                "placement": {
                    "@type": "xsd:integer",
                    "rdfs:label": "Final Placement"
                },
                "level": {
                    "@type": "xsd:integer",
                    "rdfs:label": "Final Level"
                },
                "goldLeft": {
                    "@type": "xsd:integer", 
                    "rdfs:label": "Gold Remaining"
                },
                "damageDealt": {
                    "@type": "xsd:integer",
                    "rdfs:label": "Total Damage Dealt"
                },
                "roundsEliminated": {
                    "@type": "xsd:integer",
                    "rdfs:label": "Round When Eliminated"
                },
                "starLevel": {
                    "@type": "xsd:integer",
                    "rdfs:label": "Champion Star Level"
                },
                "traitTier": {
                    "@type": "xsd:integer", 
                    "rdfs:label": "Active Trait Tier"
                },
                "queueType": {
                    "@type": "xsd:string",
                    "rdfs:label": "Queue Type"
                },
                
                "participatedIn": {
                    "@type": "@id",
                    "rdfs:label": "Participated In Match"
                },
                "hasParticipant": {
                    "@type": "@id",
                    "rdfs:label": "Has Participant"
                },
                "usedChampion": {
                    "@type": "@id", 
                    "rdfs:label": "Used Champion"
                },
                "activatedTrait": {
                    "@type": "@id",
                    "rdfs:label": "Activated Trait"
                },
                "equippedItem": {
                    "@type": "@id",
                    "rdfs:label": "Equipped Item"
                },
                "wonAgainst": {
                    "@type": "@id",
                    "rdfs:label": "Won Against"
                },
                "competedWith": {
                    "@type": "@id",
                    "rdfs:label": "Competed With"
                },
                "championProvidesTrait": {
                    "@type": "@id",
                    "rdfs:label": "Champion Provides Trait"
                },
                "itemEquippedOn": {
                    "@type": "@id",
                    "rdfs:label": "Item Equipped On Champion"
                }
            },
            
            "@graph": [
                {
                    "@id": "TFTDataCollection",
                    "@type": "rdfs:Class",
                    "rdfs:label": "TFT Data Collection",
                    "rdfs:comment": "Root collection containing all TFT data"
                },
                {
                    "@id": "TFTPlayer", 
                    "@type": "rdfs:Class",
                    "rdfs:label": "TFT Player",
                    "rdfs:comment": "Individual player in the TFT ecosystem"
                },
                {
                    "@id": "TFTMatch",
                    "@type": "rdfs:Class", 
                    "rdfs:label": "TFT Match",
                    "rdfs:comment": "Single game instance"
                }
            ]
        }
        
        return schema

    def export_schema_to_file(self, filename: str = "tft_schema.jsonld") -> None:
        """
        Export the JSON-LD schema to a file
        """
        schema = self.create_comprehensive_schema()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        
        print(f"[SUCCESS] JSON-LD schema exported to {filename}")
        
    def get_schema_context(self) -> Dict[str, Any]:
        """
        Get just the @context portion of the schema for embedding in data
        """
        full_schema = self.create_comprehensive_schema()
        return full_schema["@context"]


def create_default_schema() -> TFTSchemaGenerator:
    """
    Create a default TFT schema generator instance
    """
    return TFTSchemaGenerator()


def export_default_schema(filename: str = "tft_schema.jsonld") -> None:
    """
    Export the default TFT schema to a file
    """
    generator = create_default_schema()
    generator.export_schema_to_file(filename)


def get_tft_context() -> Dict[str, Any]:
    """
    Get the standard TFT JSON-LD context for data embedding
    """
    generator = create_default_schema()
    return generator.get_schema_context()


if __name__ == "__main__":
    print("🧪 Testing TFT JSON-LD Schema Generator")
    print("=" * 50)
    
    generator = create_default_schema()
    
    from quality_assurance.schema_validator import validate_schema_structure
    is_valid = validate_schema_structure(generator)
    print(f"Schema validation: {'[SUCCESS] PASS' if is_valid else '[ERROR] FAIL'}")
    
    generator.export_schema_to_file()
    
    schema = generator.create_comprehensive_schema()
    print(f"Schema statistics:")
    print(f"   Context definitions: {len(schema['@context'])}")
    print(f"   Class definitions: {len(schema['@graph'])}")
    print(f"   Base URI: {generator.base_uri}")
    print(f"   Schema URI: {generator.schema_uri}")
    
    print("\n🎉 TFT Schema Module Ready!")
