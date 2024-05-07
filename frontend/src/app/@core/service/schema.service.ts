import {Injectable} from "@angular/core";
import {GlobalVariable} from "../global";
import {HttpClient, HttpParams} from "@angular/common/http";
import {Observable} from "rxjs";
import {SchemaStru} from "../model/schema.model";

@Injectable()
export class SchemaService {
  private baseApiUrl = GlobalVariable.BASE_API_URL;
  private baseUserId = GlobalVariable.BASE_USER_ID;

  constructor(private http: HttpClient) { }

  getSchemaInfo(schemaId:string): Observable<SchemaStru> {
    const params = new HttpParams()
      .set('schemaId',schemaId);
    return this.http.get<SchemaStru>(this.baseApiUrl + 'schema',
      {
        params: params
      });
  }

  addSchema(userId:string, schemaName:string, minSupport: number, token: any[]): Observable<SchemaStru> {
    let id = userId;
    if (id === '') {
      id = this.baseUserId;
    }
    const params = new HttpParams()
      .set('userId',id)
      .set('schemaName',schemaName)
      .set('minSupport',minSupport.toString())
      .set('ignoreTokens',JSON.stringify(token).toString());
    return this.http.post<SchemaStru>(this.baseApiUrl + 'addSchema', params);
  }

  updateSchema(schemaId:string, minimum_support: number, token: any[]): Observable<SchemaStru> {
    const params = new HttpParams()
      .set('schemaId',schemaId)
      .set('minSupport',minimum_support.toString())
      .set('ignoreTokens',JSON.stringify(token).toString());
    return this.http.post<SchemaStru>(this.baseApiUrl + 'updateSchema', params);
  }

  updatePatternOfSchema(schemaId:string, pattern: string[]): Observable<SchemaStru>  {
    const params = new HttpParams()
      .set('schemaId', schemaId)
      .set('patternList', pattern.toString());
    return this.http.post<SchemaStru>(this.baseApiUrl + 'updatePatternOfSchema', params);
  }

  getPatterns(schemaId:string): Observable<string[]> {
    const params = new HttpParams()
      .set('schemaId',schemaId);
    return this.http.get<string[]>(this.baseApiUrl + 'patterns',
      {
        params: params
      });
  }

  getAttributes(schemaId:string): Observable<string[]> {
    const params = new HttpParams()
      .set('schemaId',schemaId);
    return this.http.get<string[]>(this.baseApiUrl + 'getAttributes',
      {
        params: params
      });
  }

  getDtd(schemaId:string): Observable<string> {
    const params = new HttpParams()
      .set('schemaId',schemaId);
    return this.http.get<string>(this.baseApiUrl + 'getDtd',
      {
        params: params
      });
  }

  updateAttributeOfSchema(schemaId:string, attribute: string): Observable<SchemaStru>  {
    const params = new HttpParams()
      .set('schemaId', schemaId)
      .set('attribute', attribute);
    return this.http.post<SchemaStru>(this.baseApiUrl + 'updateAttributeOfSchema', params);
  }

  updateDtdOfSchema(schemaId:string, dtd: string): Observable<SchemaStru>  {
    const params = new HttpParams()
      .set('schemaId', schemaId)
      .set('dtd', dtd);
    return this.http.post<SchemaStru>(this.baseApiUrl + 'updateDtdOfSchema', params);
  }

  updateFileListOfSchema(schemaId:string, filename: string, filetype: string): Observable<SchemaStru>  {
    const params = new HttpParams()
      .set('schemaId', schemaId)
      .set('filetype', filetype)
      .set('filename', filename);
    return this.http.post<SchemaStru>(this.baseApiUrl + 'updateFileListOfSchema', params);
  }

  learningRule(schemaId:string, fileId:string, structure: any, content: string, mapping: any, filetype: string): Observable<SchemaStru> {
    const params = new HttpParams()
      .set('schemaId', schemaId)
      .set('fileId', fileId)
      .set('dtd', JSON.stringify(structure).toString())
      .set('mapping', JSON.stringify(mapping).toString())
      .set('filetype', filetype)
      .set('content', content);
    return this.http.post<SchemaStru>(this.baseApiUrl + 'learningRule', params);
  }

  updatePatternsByLangchain(schemaId:string, structure: any, content: string): Observable<SchemaStru> {
    const params = new HttpParams()
      .set('schemaId', schemaId)
      .set('dtd', JSON.stringify(structure).toString())
      .set('content', content);
    return this.http.post<SchemaStru>(this.baseApiUrl + 'updatePatternsByLangchain', params);
  }
}
