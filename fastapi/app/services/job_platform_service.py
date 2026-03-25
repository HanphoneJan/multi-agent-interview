"""Job platform integration service"""
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from abc import ABC, abstractmethod

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.career import job_platforms, external_jobs, job_career_mappings
from app.config import get_settings
from app.utils.log_helper import get_logger

settings = get_settings()

logger = get_logger("services.job_platform")


class JobPlatformAdapter(ABC):
    """Abstract base class for job platform adapters"""

    @property
    @abstractmethod
    def platform_code(self) -> str:
        """Platform code identifier"""
        pass

    @abstractmethod
    async def search_jobs(
        self,
        keyword: str,
        city: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[Dict[str, Any]]:
        """Search jobs on the platform"""
        pass

    @abstractmethod
    async def get_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job detail by ID"""
        pass


class ZhaopinAdapter(JobPlatformAdapter):
    """
    智联招聘适配器

    基于 DrissionPage 的爬虫实现
    参考: archive/django/learning_manager/job_search.py
    """

    def __init__(self):
        self._platform_code = "zhaopin"
        self.base_url = "https://www.zhaopin.com"
        self.api_endpoint = "https://fe-api.zhaopin.com"

    @property
    def platform_code(self) -> str:
        return self._platform_code

    async def search_jobs(
        self,
        keyword: str,
        city: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[Dict[str, Any]]:
        """
        搜索智联招聘岗位

        注意：实际爬虫实现需要 DrissionPage，这里提供接口定义
        生产环境需要配置浏览器环境和反爬措施
        """
        logger.info(f"Searching Zhaopin jobs: keyword={keyword}, city={city}")

        # 城市编码映射
        city_codes = {
            "上海": 538, "北京": 530, "广州": 763, "深圳": 765,
            "天津": 531, "武汉": 736, "西安": 854, "成都": 801,
            "南京": 635, "杭州": 653, "重庆": 551, "厦门": 682,
        }
        city_code = city_codes.get(city, 489)  # 489 = 全国

        try:
            # 尝试使用爬虫获取数据
            jobs = await self._crawl_jobs(keyword, city_code, page, page_size)
            return jobs
        except Exception as e:
            logger.warning(f"Zhaopin crawl failed: {e}, returning empty list")
            return []

    async def _crawl_jobs(
        self,
        keyword: str,
        city_code: int,
        page: int,
        page_size: int
    ) -> List[Dict[str, Any]]:
        """
        使用 DrissionPage 爬取岗位数据

        这是一个异步包装器，实际的爬虫在同步函数中执行
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,  # 使用默认线程池
            self._sync_crawl_jobs,
            keyword,
            city_code,
            page,
            page_size
        )

    def _sync_crawl_jobs(
        self,
        keyword: str,
        city_code: int,
        page: int,
        page_size: int
    ) -> List[Dict[str, Any]]:
        """
        同步爬虫实现（参考 archive/django/learning_manager/job_search.py）
        """
        try:
            from DrissionPage import ChromiumPage, ChromiumOptions
        except ImportError:
            logger.error("DrissionPage not installed, cannot crawl Zhaopin")
            return []

        jobs = []

        try:
            # 创建浏览器配置
            co = ChromiumOptions()
            # 无头模式在生产环境使用
            # co.headless(True)

            # 创建页面对象
            page = ChromiumPage(co)

            # 监听 API 响应
            page.listen.start('/search/positions')

            # 构建搜索 URL
            search_url = f'https://www.zhaopin.com/sou/jl{city_code}/p{page}'
            page.get(search_url)

            # 输入关键词
            import time
            time.sleep(2)

            # 查找搜索框并输入
            try:
                search_input = page.ele('css:.query-search__content-input')
                search_input.input(keyword)

                # 点击搜索按钮
                search_btn = page.ele('css:.query-search__content-button')
                search_btn.click()

                # 等待响应
                time.sleep(3)

                # 获取响应数据
                resp = page.listen.wait()
                json_data = resp.response.body

                if json_data and 'data' in json_data:
                    job_list = json_data['data'].get('list', [])

                    for item in job_list[:page_size]:
                        job = {
                            'external_id': str(item.get('number', '')),
                            'title': item.get('name', ''),
                            'company_name': item.get('companyName', ''),
                            'salary_text': item.get('salary60', ''),
                            'city': item.get('workCity', ''),
                            'district': item.get('cityDistrict', ''),
                            'education_requirement': item.get('education', ''),
                            'experience_requirement': item.get('workingExp', ''),
                            'job_tags': item.get('skillLabel', []),
                            'company_size': item.get('companySize', ''),
                            'company_url': item.get('companyUrl', ''),
                            'apply_url': item.get('applyUrl', ''),
                            'publish_date': item.get('publishTime', ''),
                            'raw_data': item,
                        }
                        jobs.append(job)

            except Exception as e:
                logger.error(f"Error during Zhaopin crawling: {e}")

            finally:
                page.quit()

        except Exception as e:
            logger.error(f"Failed to initialize Zhaopin crawler: {e}")

        return jobs

    async def get_job_detail(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job detail from Zhaopin"""
        # 实现职位详情爬取
        logger.info(f"Getting Zhaopin job detail: {job_id}")
        return None


class JobPlatformService:
    """Job platform integration service"""

    def __init__(self):
        self.adapters: Dict[str, JobPlatformAdapter] = {
            "zhaopin": ZhaopinAdapter(),
        }

    async def search_jobs(
        self,
        db: AsyncSession,
        keyword: str,
        city: Optional[str] = None,
        platforms: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search jobs across multiple platforms

        Args:
            db: Database session
            keyword: Search keyword
            city: City name
            platforms: List of platform codes to search, None for all active
            page: Page number
            page_size: Items per page

        Returns:
            List of job dictionaries
        """
        # Get active platforms from database if not specified
        if not platforms:
            platform_list = await self._get_active_platforms(db)
            platforms = [p['code'] for p in platform_list]

        all_jobs = []

        # Search each platform
        for platform_code in platforms:
            adapter = self.adapters.get(platform_code)
            if not adapter:
                logger.warning(f"Unknown platform: {platform_code}")
                continue

            try:
                jobs = await adapter.search_jobs(keyword, city, page, page_size)
                for job in jobs:
                    job['platform_code'] = platform_code
                    job['_source'] = 'external'
                all_jobs.extend(jobs)
            except Exception as e:
                logger.error(f"Error searching {platform_code}: {e}")

        # Also search local cached jobs
        local_jobs = await self._search_local_jobs(db, keyword, city, page_size)
        all_jobs.extend(local_jobs)

        # Sort by publish date if available
        all_jobs.sort(
            key=lambda x: x.get('publish_date', ''),
            reverse=True
        )

        return all_jobs[:page_size]

    async def sync_jobs(
        self,
        db: AsyncSession,
        platform_code: str,
        keyword: Optional[str] = None,
        max_jobs: int = 100
    ) -> int:
        """
        Sync jobs from platform to local database

        Args:
            db: Database session
            platform_code: Platform code
            keyword: Search keyword, None for default keywords
            max_jobs: Maximum jobs to sync

        Returns:
            Number of jobs synced
        """
        adapter = self.adapters.get(platform_code)
        if not adapter:
            raise ValueError(f"Unknown platform: {platform_code}")

        # Get platform ID from database
        platform = await self._get_platform_by_code(db, platform_code)
        if not platform:
            raise ValueError(f"Platform not configured: {platform_code}")

        # Default keywords if not provided
        keywords = [keyword] if keyword else [
            "后端开发", "前端开发", "算法工程师",
            "数据分析师", "产品经理", "运维工程师"
        ]

        synced_count = 0

        for kw in keywords:
            if synced_count >= max_jobs:
                break

            try:
                jobs = await adapter.search_jobs(kw, page_size=20)

                for job_data in jobs:
                    if synced_count >= max_jobs:
                        break

                    # Check if job already exists
                    existing = await self._get_job_by_external_id(
                        db, platform['id'], job_data['external_id']
                    )

                    if existing:
                        # Update existing job
                        await self._update_job(db, existing['id'], job_data)
                    else:
                        # Create new job
                        await self._create_job(db, platform['id'], job_data)
                        synced_count += 1

                await db.commit()

            except Exception as e:
                logger.error(f"Error syncing jobs for keyword '{kw}': {e}")
                await db.rollback()

        # Update platform last_sync_at
        await self._update_platform_sync_time(db, platform['id'])

        logger.info(f"Synced {synced_count} jobs from {platform_code}")
        return synced_count

    async def get_salary_statistics(
        self,
        db: AsyncSession,
        career_id: int,
        city: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get salary statistics for a career

        Args:
            db: Database session
            career_id: Career ID
            city: Optional city filter

        Returns:
            Salary statistics dictionary
        """
        # Get external jobs for this career
        query = select(external_jobs).where(
            and_(
                external_jobs.c.career_id == career_id,
                external_jobs.c.is_active == True,
                external_jobs.c.salary_min.isnot(None),
                external_jobs.c.salary_max.isnot(None)
            )
        )

        if city:
            query = query.where(external_jobs.c.city == city)

        result = await db.execute(query)
        jobs = [dict(row._mapping) for row in result]

        if not jobs:
            return {
                "count": 0,
                "avg_salary_min": None,
                "avg_salary_max": None,
                "median_salary": None,
                "by_experience": {},
                "by_city": {}
            }

        # Calculate statistics
        salaries_min = [j['salary_min'] for j in jobs if j.get('salary_min')]
        salaries_max = [j['salary_max'] for j in jobs if j.get('salary_max')]

        avg_min = sum(salaries_min) / len(salaries_min) if salaries_min else 0
        avg_max = sum(salaries_max) / len(salaries_max) if salaries_max else 0

        # Group by experience
        by_experience = {}
        for job in jobs:
            exp = job.get('experience_requirement', '未知')
            if exp not in by_experience:
                by_experience[exp] = {
                    "count": 0,
                    "avg_salary_min": 0,
                    "avg_salary_max": 0
                }
            by_experience[exp]["count"] += 1
            if job.get('salary_min'):
                by_experience[exp]["avg_salary_min"] += job['salary_min']
            if job.get('salary_max'):
                by_experience[exp]["avg_salary_max"] += job['salary_max']

        # Calculate averages
        for exp in by_experience:
            count = by_experience[exp]["count"]
            if count > 0:
                by_experience[exp]["avg_salary_min"] //= count
                by_experience[exp]["avg_salary_max"] //= count

        # Group by city
        by_city = {}
        for job in jobs:
            city_name = job.get('city', '未知')
            if city_name not in by_city:
                by_city[city_name] = {"count": 0, "avg_salary": 0}
            by_city[city_name]["count"] += 1
            if job.get('salary_min') and job.get('salary_max'):
                by_city[city_name]["avg_salary"] += (job['salary_min'] + job['salary_max']) // 2

        for city_name in by_city:
            if by_city[city_name]["count"] > 0:
                by_city[city_name]["avg_salary"] //= by_city[city_name]["count"]

        return {
            "count": len(jobs),
            "avg_salary_min": int(avg_min),
            "avg_salary_max": int(avg_max),
            "median_salary": int((avg_min + avg_max) // 2),
            "by_experience": by_experience,
            "by_city": by_city
        }

    # Private helper methods

    async def _get_active_platforms(self, db: AsyncSession) -> List[Dict]:
        """Get active job platforms from database"""
        result = await db.execute(
            select(job_platforms).where(job_platforms.c.is_active == True)
        )
        return [dict(row._mapping) for row in result]

    async def _get_platform_by_code(
        self,
        db: AsyncSession,
        code: str
    ) -> Optional[Dict]:
        """Get platform by code"""
        result = await db.execute(
            select(job_platforms).where(job_platforms.c.code == code)
        )
        row = result.first()
        return dict(row._mapping) if row else None

    async def _search_local_jobs(
        self,
        db: AsyncSession,
        keyword: str,
        city: Optional[str],
        limit: int
    ) -> List[Dict]:
        """Search local cached jobs"""
        from sqlalchemy import or_

        query = select(external_jobs).where(
            and_(
                external_jobs.c.is_active == True,
                or_(
                    external_jobs.c.title.ilike(f"%{keyword}%"),
                    external_jobs.c.job_description.ilike(f"%{keyword}%")
                )
            )
        )

        if city:
            query = query.where(external_jobs.c.city == city)

        query = query.order_by(
            external_jobs.c.publish_date.desc()
        ).limit(limit)

        result = await db.execute(query)
        jobs = []
        for row in result:
            job = dict(row._mapping)
            job['_source'] = 'local'
            jobs.append(job)

        return jobs

    async def _get_job_by_external_id(
        self,
        db: AsyncSession,
        platform_id: int,
        external_id: str
    ) -> Optional[Dict]:
        """Get job by external ID"""
        result = await db.execute(
            select(external_jobs).where(
                and_(
                    external_jobs.c.platform_id == platform_id,
                    external_jobs.c.external_id == external_id
                )
            )
        )
        row = result.first()
        return dict(row._mapping) if row else None

    async def _create_job(
        self,
        db: AsyncSession,
        platform_id: int,
        job_data: Dict[str, Any]
    ):
        """Create a new external job record"""
        from sqlalchemy.dialects.postgresql import insert

        # Parse salary text
        salary_min, salary_max = self._parse_salary(job_data.get('salary_text', ''))

        stmt = insert(external_jobs).values(
            platform_id=platform_id,
            external_id=job_data['external_id'],
            title=job_data['title'],
            company_name=job_data.get('company_name'),
            salary_min=salary_min,
            salary_max=salary_max,
            city=job_data.get('city'),
            district=job_data.get('district'),
            education_requirement=job_data.get('education_requirement'),
            experience_requirement=job_data.get('experience_requirement'),
            job_description=job_data.get('job_description'),
            job_tags=job_data.get('job_tags', []),
            skills_required=job_data.get('skills_required', []),
            apply_url=job_data.get('apply_url'),
            publish_date=job_data.get('publish_date'),
            raw_data=job_data.get('raw_data'),
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        await db.execute(stmt)

    async def _update_job(
        self,
        db: AsyncSession,
        job_id: int,
        job_data: Dict[str, Any]
    ):
        """Update an existing job record"""
        from sqlalchemy import update

        salary_min, salary_max = self._parse_salary(job_data.get('salary_text', ''))

        stmt = update(external_jobs).where(
            external_jobs.c.id == job_id
        ).values(
            title=job_data['title'],
            company_name=job_data.get('company_name'),
            salary_min=salary_min,
            salary_max=salary_max,
            city=job_data.get('city'),
            education_requirement=job_data.get('education_requirement'),
            experience_requirement=job_data.get('experience_requirement'),
            job_tags=job_data.get('job_tags', []),
            apply_url=job_data.get('apply_url'),
            updated_at=datetime.now(timezone.utc)
        )
        await db.execute(stmt)

    async def _update_platform_sync_time(self, db: AsyncSession, platform_id: int):
        """Update platform last sync time"""
        from sqlalchemy import update

        stmt = update(job_platforms).where(
            job_platforms.c.id == platform_id
        ).values(
            last_sync_at=datetime.now(timezone.utc)
        )
        await db.execute(stmt)
        await db.commit()

    def _parse_salary(self, salary_text: str) -> tuple:
        """Parse salary text like '15K-20K' or '15000-20000' to integers"""
        try:
            import re

            if not salary_text:
                return None, None

            # Remove spaces and standardize
            salary_text = salary_text.replace(' ', '').upper()

            # Extract numbers
            numbers = re.findall(r'(\d+)', salary_text)

            if len(numbers) >= 2:
                min_sal = int(numbers[0])
                max_sal = int(numbers[1])

                # Handle K (thousands)
                if 'K' in salary_text or '千' in salary_text:
                    min_sal *= 1000
                    max_sal *= 1000

                return min_sal, max_sal

            elif len(numbers) == 1:
                sal = int(numbers[0])
                if 'K' in salary_text or '千' in salary_text:
                    sal *= 1000
                return sal, sal

        except Exception as e:
            logger.warning(f"Failed to parse salary '{salary_text}': {e}")

        return None, None


# Global service instance
job_platform_service = JobPlatformService()
