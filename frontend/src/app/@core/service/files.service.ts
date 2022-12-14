import {Injectable} from "@angular/core";
import {GlobalVariable} from "../global";
import {HttpClient, HttpParams} from "@angular/common/http";
import {Observable} from "rxjs";
import {FileInfoStru} from "../model/files.model";

@Injectable()
export class FilesService {
  private baseApiUrl = GlobalVariable.BASE_API_URL;

  constructor(private http: HttpClient) {
  }

  addFileInfo(schemaId:string, fileId:string, dtd: string): Observable<FileInfoStru> {
    const params = new HttpParams()
      .set('schemaId',schemaId)
      .set('fileId',fileId)
      .set('dtd',dtd);
    return this.http.post<FileInfoStru>(this.baseApiUrl + 'addFileInfo', params);
  }

  getFileInfo(schemaId:string, fileId:string): Observable<FileInfoStru> {
    const params = new HttpParams()
      .set('schema_id',schemaId)
      .set('file_id',fileId);
    return this.http.get<FileInfoStru>(this.baseApiUrl + 'getFileInfo', {
        params: params
      });
  }

  updateStructureById(schemaId:string, fileId:string, structure: any, pc: any): Observable<FileInfoStru> {
    const params = new HttpParams()
      .set('schemaId', schemaId)
      .set('fileId', fileId)
      .set('dtd', JSON.stringify(structure).toString())
      .set('pc', JSON.stringify(pc).toString());
    return this.http.post<FileInfoStru>(this.baseApiUrl + 'updateStructureById', params);
  }
}
