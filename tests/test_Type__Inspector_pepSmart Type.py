      #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySmart v1.0 - Smart Type Inspector & Differ (Mypy Companion)
Auteur : Aissa Mohammedi (DGK) - NEXUS-OPEN-3.0
Rôle : Analyser, diffuser et upgrader les définitions de types Python (TypedDict, Dataclass).
"""

import ast
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

class TypeVisitor(ast.NodeVisitor):
    """Visiteur AST pour extraire les types complexes."""
    def __init__(self):
        self.types = {}

    def visit_ClassDef(self, node: ast.ClassDef):
        # Détection des TypedDict et Dataclass
        decorators = [ast.unparse(d) for d in node.decorator_list]
        if "TypedDict" in decorators or "dataclass" in decorators:
            fields = {}
            for item in node.body:
                if isinstance(item, ast.AnnAssign):
                    field_name = item.target.id
                    field_type = ast.unparse(item.annotation)
                    fields[field_name] = field_type
            self.types[node.name] = {
                "type": "TypedDict" if "TypedDict" in decorators else "Dataclass",
                "fields": fields,
                "lineno": node.lineno
            }
        self.generic_visit(node)

def extract_types_from_file(filepath: str) -> Dict[str, Any]:
    """Extrait les types d'un fichier Python."""
    try:
        source = Path(filepath).read_text(encoding="utf-8")
        tree = ast.parse(source)
        visitor = TypeVisitor()
        visitor.visit(tree)
        return visitor.types
    except Exception as e:
        print(f"Erreur de lecture {filepath}: {e}")
        return {}

def diff_types(old_types: Dict, new_types: Dict) -> Dict[str, List[str]]:
    """Génère un diff intelligent entre deux versions de types (Style SmartGit)."""
    diff = {"added": [], "removed": [], "modified": []}

    for type_name in new_types:
        if type_name not in old_types:
            diff["added"].append(type_name)
        else:
            old_fields = old_types[type_name]["fields"]
            new_fields = new_types[type_name]["fields"]
            
            changes = []
            for field, ftype in new_fields.items():
                if field not in old_fields:
                    changes.append(f"+ {field}: {ftype}")
                elif old_fields[field] != ftype:
                    changes.append(f"~ {field}: {old_fields[field]} -> {ftype}")
            for field in old_fields:
                if field not in new_fields:
                    changes.append(f"- {field}")
            
            if changes:
                diff["modified"].append({"type": type_name, "changes": changes})

    for type_name in old_types:
        if type_name not in new_types:
            diff["removed"].append(type_name)

    return diff

def smart_type_inspector(action: str, file_a: str, file_b: Optional[str] = None):
    """Fonction principale de l'outil PySmart."""
    print(f"\033[1;36m[*] PySmart Engine - Action: {action}\033[0m")
    
    types_a = extract_types_from_file(file_a)
    
    if action == "analyze":
        print(f"Fichier : {file_a}")
        print(json.dumps(types_a, indent=2, ensure_ascii=False))
        
    elif action == "diff" and file_b:
        types_b = extract_types_from_file(file_b)
        diff = diff_types(types_a, types_b)
        
        print(f"\n\033[1;33mDiff de Types : {file_a} -> {file_b}\033[0m")
        if diff["added"]:
            print(f"\033[1;32m[+] TypedDict ajoutés : {', '.join(diff['added'])}\033[0m")
        if diff["removed"]:
            print(f"\033[1;31m[-] TypedDict supprimés : {', '.join(diff['removed'])}\033[0m")
        for mod in diff["modified"]:
            print(f"\n\033[1;34m[~] Modifié : {mod['type']}\033[0m")
            for change in mod["changes"]:
                color = "\033[1;32m" if change.startswith("+") else "\033[1;31m" if change.startswith("-") else "\033[1;33m"
                print(f"    {color}{change}\033[0m")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python pysmart.py <analyze|diff> <fichier1.py> [fichier2.py]")
        sys.exit(1)
    
    action = sys.argv[1]
    file_a = sys.argv[2]
    file_b = sys.argv[3] if len(sys.argv) > 3 else None
    
    smart_type_inspector(action, file_a, file_b)
