export interface FileInfo {id:string;name:string;size:number;mime_type:string;type:string;extension:string;modified:boolean}
export interface MetadataField {group:string;name:string;fullName:string;displayName:string;value:unknown;editable:boolean;suggested:boolean;helpText:string|null;valueType:'text'|'number'|'boolean'|'date'|'long_text'}
export interface FileMetadata {file:FileInfo;metadata:MetadataField[]}
export interface PrivacyItem {category:string;label:string;severity:'low'|'medium'|'high';tags:string[]}
export interface Health {status:string;exiftool:{available:boolean;version:string|null;executable?:string|null}}
export interface ApiError {error:{code:string;message:string;details:string|null}}
export type Theme='light'|'dark'|'system'; export type Filter='all'|'filled'|'editable'|'favorites';
